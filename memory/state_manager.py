"""Immutable state management utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Optional

from pydantic import BaseModel

from memory.models import (
    AlternativeOption,
    DesiredReservation,
    GlobalMemory,
    ReservationDetails,
    SemanticMemory,
)
from shared.enums import (
    AvailabilityStatus,
    ConfirmationStatus,
    SkillName,
    WorkflowStage,
)

if TYPE_CHECKING:  # pragma: no cover
    from skills.outputs import (
        AlternativeProposalOutput,
        AvailabilitySkillOutput,
        ConfirmationSkillOutput,
        DetailsCollectionOutput,
        ErrorRecoveryOutput,
        GreetingSkillOutput,
        MenuDiscussionOutput,
    )

UpdateHandler = Callable[[GlobalMemory, BaseModel], None]


def _get_next_missing_field(state: GlobalMemory) -> Optional[str]:
    """Get the first missing required field in order: party_size, contact_name, contact_phone."""
    cf = state.workflow.confirmed_fields
    required_fields = ["party_size", "contact_name", "contact_phone", "date", "time"]
    for field in required_fields:
        if not getattr(cf, field):
            return field
    return None


def _set_next_field_under_review(state: GlobalMemory) -> None:
    """Set field_under_review to the next missing field."""
    state.working.field_under_review = _get_next_missing_field(state)


def create_initial_state(
    semantic_memory: Optional[SemanticMemory] = None,
    desired_reservation: Optional[DesiredReservation] = None,
) -> GlobalMemory:
    """Return a fully initialized memory tree for a new session.

    Args:
        semantic_memory: Optional SemanticMemory with custom guest/restaurant data.
        desired_reservation: Optional DesiredReservation with custom booking preferences.

    Returns:
        A fully initialized GlobalMemory state.
    """
    state = GlobalMemory()

    # Apply custom semantic memory if provided
    if semantic_memory is not None:
        state.semantic = semantic_memory

    # Apply custom desired reservation if provided
    if desired_reservation is not None:
        state.semantic.desired_reservation = desired_reservation

    # Initialize working memory with goal reservation from semantic memory
    desired = state.semantic.desired_reservation
    state.working.goal_reservation = ReservationDetails(
        date=desired.date,
        time=desired.time,
        party_size=desired.party_size,
        occasion=desired.occasion,
        special_requests=desired.special_requests,
        contact_name=state.semantic.guest_name,
        contact_phone=state.semantic.guest_phone,
    )
    return state


def record_user_turn(state: GlobalMemory, message: str) -> GlobalMemory:
    """Append a user utterance in an immutable fashion."""

    new_state = state.model_copy(deep=True)
    new_state.append_turn("user", message)
    return new_state


def apply_skill_output(
    state: GlobalMemory, skill_name: SkillName, output: BaseModel
) -> GlobalMemory:
    """Apply the structured output of a skill to the memory tree."""

    new_state = state.model_copy(deep=True)
    handler = _HANDLERS.get(skill_name)
    if handler:
        handler(new_state, output)
    return new_state


def _handle_greeting(state: GlobalMemory, output: "GreetingSkillOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.workflow.stage = WorkflowStage.SHARE_PREFERENCES
    state.working.pending_questions = []


def _handle_availability(
    state: GlobalMemory, output: "AvailabilitySkillOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    workflow.availability_status = output.availability_status
    workflow.selected_slot_note = output.selected_slot_note
    workflow.blocking_issue = None
    state.working.pending_questions = output.pending_questions

    if output.suggested_alternatives:
        state.working.proposed_alternatives = [
            AlternativeOption(description=alt, accepted=False)
            for alt in output.suggested_alternatives
        ]
    elif output.availability_status == AvailabilityStatus.SLOT_ACCEPTED:
        state.working.proposed_alternatives = []
        # Mark date and time as confirmed when slot is accepted
        workflow.confirmed_fields.date = True
        workflow.confirmed_fields.time = True

    if output.availability_status == AvailabilityStatus.SLOT_ACCEPTED:
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        # Set field_under_review to first missing required field
        _set_next_field_under_review(state)
    elif output.availability_status == AvailabilityStatus.WAITING_ON_STAFF:
        workflow.stage = WorkflowStage.AWAIT_AVAILABILITY
    elif output.availability_status == AvailabilityStatus.ALTERNATIVES_OFFERED:
        workflow.stage = WorkflowStage.REVIEW_ALTERNATIVES
    elif output.availability_status == AvailabilityStatus.DECLINED:
        workflow.stage = WorkflowStage.REVIEW_ALTERNATIVES
    else:
        workflow.stage = WorkflowStage.SHARE_PREFERENCES


def _handle_details(state: GlobalMemory, output: "DetailsCollectionOutput") -> None:
    """Collect reservation details one field at a time."""
    state.append_turn("agent", output.ai_response)
    details_payload = output.reservation_details or ReservationDetails()
    details_payload.contact_name = (
        details_payload.contact_name or state.semantic.guest_name
    )
    details_payload.contact_phone = (
        details_payload.contact_phone or state.semantic.guest_phone
    )
    workflow = state.workflow

    # Mark confirmed fields based on what was just collected
    # Only mark the field that was under review
    field_under_review = state.working.field_under_review

    if field_under_review == "date" and details_payload.date is not None:
        workflow.confirmed_fields.date = True
    elif field_under_review == "time" and details_payload.time is not None:
        workflow.confirmed_fields.time = True
    elif field_under_review == "party_size" and details_payload.party_size is not None:
        workflow.confirmed_fields.party_size = True
    elif field_under_review == "contact_name" and details_payload.contact_name:
        workflow.confirmed_fields.contact_name = True
    elif field_under_review == "contact_phone" and details_payload.contact_phone:
        workflow.confirmed_fields.contact_phone = True
    elif field_under_review == "occasion" and details_payload.occasion:
        workflow.confirmed_fields.occasion = True
    elif field_under_review == "special_requests" and details_payload.special_requests:
        workflow.confirmed_fields.special_requests = True

    # Move to next stage only when all required fields are confirmed
    if workflow.confirmed_fields.all_required_confirmed():
        if output.needs_menu_dialog:
            workflow.stage = WorkflowStage.MENU_DISCUSSION
        else:
            workflow.stage = WorkflowStage.AWAIT_CONFIRMATION
    else:
        # Stay in PROVIDE_CONTACT and set next field under review
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        _set_next_field_under_review(state)


def _handle_menu(state: GlobalMemory, output: "MenuDiscussionOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.working.menu_preferences = output.menu_preferences
    workflow = state.workflow
    workflow.stage = output.next_stage


def _handle_confirmation(
    state: GlobalMemory, output: "ConfirmationSkillOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    workflow.confirmation_status = output.confirmation_status
    workflow.blocking_issue = (
        output.error_message
        if output.confirmation_status == ConfirmationStatus.PENDING
        else None
    )
    if output.booking_reference:
        workflow.selected_slot_note = output.booking_reference

    if output.confirmation_status == ConfirmationStatus.CONFIRMED_BY_STAFF:
        # Mark all fields as confirmed
        workflow.confirmed_fields.date = True
        workflow.confirmed_fields.time = True
        workflow.confirmed_fields.party_size = True
        workflow.confirmed_fields.contact_name = True
        workflow.confirmed_fields.contact_phone = True
        workflow.stage = WorkflowStage.WRAP_UP
        state.working.confirmed_reservation = output.confirmed_reservation
        state.working.pending_questions = []
    elif output.confirmation_status == ConfirmationStatus.NEEDS_CLARIFICATION:
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        state.working.pending_questions = (
            [output.error_message] if output.error_message else []
        )
        workflow.blocking_issue = None
        # Extract which field needs clarification and mark it as not confirmed
        error_msg = output.error_message or ""
        if "date" in error_msg.lower():
            workflow.confirmed_fields.date = False
        if "time" in error_msg.lower():
            workflow.confirmed_fields.time = False
        if "phone" in error_msg.lower():
            workflow.confirmed_fields.contact_phone = False
        if "name" in error_msg.lower():
            workflow.confirmed_fields.contact_name = False
        # Set field_under_review to the next missing field
        _set_next_field_under_review(state)
    else:
        workflow.stage = WorkflowStage.AWAIT_CONFIRMATION


def _handle_alternative(
    state: GlobalMemory, output: "AlternativeProposalOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow

    if output.alternative_selected and output.accepted_slot_description:
        workflow.availability_status = AvailabilityStatus.SLOT_ACCEPTED
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        workflow.selected_slot_note = output.accepted_slot_description
        # Mark date and time as confirmed for the new alternative slot
        workflow.confirmed_fields.date = True
        workflow.confirmed_fields.time = True
        state.working.proposed_alternatives = [
            AlternativeOption(
                description=output.accepted_slot_description,
                notes="accepted by guest",
                accepted=True,
            )
        ]
        # Set field_under_review to next missing field
        _set_next_field_under_review(state)
    else:
        workflow.availability_status = AvailabilityStatus.ALTERNATIVES_OFFERED
        if output.should_end_conversation:
            workflow.stage = WorkflowStage.END
        else:
            workflow.stage = WorkflowStage.AWAIT_AVAILABILITY


def _handle_error_recovery(state: GlobalMemory, output: "ErrorRecoveryOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.workflow.stage = output.reset_stage
    state.workflow.blocking_issue = None
    state.workflow.confirmation_status = ConfirmationStatus.PENDING


_HANDLERS: Dict[SkillName, UpdateHandler] = {
    SkillName.GREETING: _handle_greeting,
    SkillName.AVAILABILITY: _handle_availability,
    SkillName.DETAILS_COLLECTION: _handle_details,
    SkillName.MENU_DISCUSSION: _handle_menu,
    SkillName.CONFIRMATION: _handle_confirmation,
    SkillName.ALTERNATIVE: _handle_alternative,
    SkillName.ERROR_RECOVERY: _handle_error_recovery,
}
