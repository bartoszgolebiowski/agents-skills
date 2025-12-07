"""Immutable state management utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from pydantic import BaseModel

from memory.models import (
    AlternativeOption,
    DesiredReservation,
    GlobalMemory,
    ReservationDetails,
    SemanticMemory,
    WorkflowMemory,
)
from persistence.json_saver import save_reservation_snapshot
from shared.enums import (
    AvailabilityStatus,
    ConfirmationStatus,
    DiscussionTopic,
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
        SaveReservationOutput,
        MenuDiscussionOutput,
    )

UpdateHandler = Callable[[GlobalMemory, BaseModel], None]


def _get_missing_explicit_confirmations(
    state: GlobalMemory, confirmed: ReservationDetails
) -> List[str]:
    """Return critical fields that still need explicit staff confirmation."""

    missing: List[str] = []
    for field in ("date", "time", "party_size"):
        if getattr(confirmed, field) is None:
            missing.append(field)

    requested_special = state.working.goal_reservation.special_requests
    if requested_special:
        special_value = (confirmed.special_requests or "").strip()
        if not special_value:
            missing.append("special_requests")

    return missing


_CONTACT_FIELD_PRIORITY = [
    "party_size",
    "contact_name",
    "contact_phone",
    "occasion",
    "special_requests",
    "date",
    "time",
]

_FIELD_TOPIC_MAP = {
    "date": DiscussionTopic.CONFIRMING_DATE,
    "time": DiscussionTopic.CONFIRMING_TIME,
    "party_size": DiscussionTopic.CONFIRMING_PARTY_SIZE,
    "special_requests": DiscussionTopic.CONFIRMING_SPECIAL_REQUESTS,
    "contact_name": DiscussionTopic.CONFIRMING_CONTACT_DETAILS,
    "contact_phone": DiscussionTopic.CONFIRMING_CONTACT_DETAILS,
    "occasion": DiscussionTopic.CONFIRMING_OCCASION,
}


def _get_next_missing_field(workflow: WorkflowMemory) -> Optional[str]:
    for field in _CONTACT_FIELD_PRIORITY:
        if not getattr(workflow.confirmed_fields, field):
            return field
    return None


def _topic_from_field(field_name: Optional[str]) -> DiscussionTopic:
    if not field_name:
        return DiscussionTopic.CONFIRMING_CONTACT_DETAILS
    return _FIELD_TOPIC_MAP.get(field_name, DiscussionTopic.CONFIRMING_CONTACT_DETAILS)


def _sync_topic_with_stage(
    workflow: WorkflowMemory, next_missing_field: Optional[str] = None
) -> None:
    if workflow.blocking_issue:
        workflow.current_topic = DiscussionTopic.ERROR_RECOVERY
        return

    stage = workflow.stage
    if stage == WorkflowStage.INTRO:
        workflow.current_topic = DiscussionTopic.GREETING
    elif stage in {
        WorkflowStage.SHARE_PREFERENCES,
        WorkflowStage.AWAIT_AVAILABILITY,
        WorkflowStage.REVIEW_ALTERNATIVES,
    }:
        workflow.current_topic = DiscussionTopic.CONFIRMING_AVAILABILITY
    elif stage == WorkflowStage.PROVIDE_CONTACT:
        workflow.current_topic = _topic_from_field(next_missing_field)
    elif stage == WorkflowStage.MENU_DISCUSSION:
        workflow.current_topic = DiscussionTopic.MENU_DISCUSSION
    elif stage == WorkflowStage.AWAIT_CONFIRMATION:
        workflow.current_topic = DiscussionTopic.CONFIRMATION
    elif stage in {WorkflowStage.SAVE_DATA, WorkflowStage.WRAP_UP, WorkflowStage.END}:
        workflow.current_topic = DiscussionTopic.CLOSING
    else:
        workflow.current_topic = DiscussionTopic.NONE


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
    _sync_topic_with_stage(state.workflow)
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
    _sync_topic_with_stage(state.workflow)


def _handle_availability(
    state: GlobalMemory, output: "AvailabilitySkillOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    workflow.availability_status = output.availability_status
    workflow.selected_slot_note = output.selected_slot_note
    workflow.blocking_issue = None
    state.working.pending_questions = output.pending_questions

    if getattr(output, "special_request_rejected", False):
        workflow.stage = WorkflowStage.WRAP_UP
        workflow.blocking_issue = "special_request_rejected"
        workflow.current_topic = DiscussionTopic.CONFIRMING_SPECIAL_REQUESTS
        state.working.proposed_alternatives = []
        return

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
    elif output.availability_status == AvailabilityStatus.WAITING_ON_STAFF:
        workflow.stage = WorkflowStage.AWAIT_AVAILABILITY
    elif output.availability_status == AvailabilityStatus.ALTERNATIVES_OFFERED:
        workflow.stage = WorkflowStage.REVIEW_ALTERNATIVES
    elif output.availability_status == AvailabilityStatus.DECLINED:
        workflow.stage = WorkflowStage.REVIEW_ALTERNATIVES
    else:
        workflow.stage = WorkflowStage.SHARE_PREFERENCES

    next_missing = None
    if workflow.stage == WorkflowStage.PROVIDE_CONTACT:
        next_missing = _get_next_missing_field(workflow)
    _sync_topic_with_stage(workflow, next_missing)


def _handle_details(state: GlobalMemory, output: "DetailsCollectionOutput") -> None:
    """Collect reservation details one field at a time."""
    state.append_turn("agent", output.ai_response)
    incoming_details = output.reservation_details or ReservationDetails()
    workflow = state.workflow

    def _mark_if_present(field_name: str, value: Optional[object]) -> None:
        if value is not None and not getattr(workflow.confirmed_fields, field_name):
            setattr(workflow.confirmed_fields, field_name, True)

    _mark_if_present("date", incoming_details.date)
    _mark_if_present("time", incoming_details.time)
    _mark_if_present("party_size", incoming_details.party_size)
    _mark_if_present("contact_name", incoming_details.contact_name)
    _mark_if_present("contact_phone", incoming_details.contact_phone)
    _mark_if_present("occasion", incoming_details.occasion)
    _mark_if_present("special_requests", incoming_details.special_requests)

    next_missing = _get_next_missing_field(workflow)

    # Move to next stage only when all required fields are confirmed
    if workflow.confirmed_fields.all_required_confirmed():
        if output.needs_menu_dialog:
            workflow.stage = WorkflowStage.MENU_DISCUSSION
            _sync_topic_with_stage(workflow)
        else:
            workflow.stage = WorkflowStage.AWAIT_CONFIRMATION
            _sync_topic_with_stage(workflow)
    else:
        # Stay in PROVIDE_CONTACT until every required field is explicitly confirmed
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        _sync_topic_with_stage(workflow, next_missing)


def _handle_menu(state: GlobalMemory, output: "MenuDiscussionOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.working.menu_preferences = output.menu_preferences
    workflow = state.workflow
    workflow.stage = output.next_stage
    _sync_topic_with_stage(workflow)


def _handle_confirmation(
    state: GlobalMemory, output: "ConfirmationSkillOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    topic_missing_field: Optional[str] = None
    workflow.confirmation_status = output.confirmation_status
    workflow.blocking_issue = (
        output.error_message
        if output.confirmation_status == ConfirmationStatus.PENDING
        else None
    )
    if output.booking_reference:
        workflow.selected_slot_note = output.booking_reference

    workflow.missing_explicit_confirmations = []
    state.working.confirmed_reservation = output.confirmed_reservation

    if output.confirmation_status == ConfirmationStatus.CONFIRMED_BY_STAFF:
        missing_fields = _get_missing_explicit_confirmations(
            state, output.confirmed_reservation
        )
        if missing_fields:
            workflow.confirmation_status = ConfirmationStatus.PENDING
            workflow.missing_explicit_confirmations = missing_fields
            workflow.stage = WorkflowStage.AWAIT_CONFIRMATION
            state.working.pending_questions = []
            _sync_topic_with_stage(workflow)
            return
        # Mark all fields as confirmed
        workflow.confirmed_fields.date = True
        workflow.confirmed_fields.time = True
        workflow.confirmed_fields.party_size = True
        workflow.confirmed_fields.contact_name = True
        workflow.confirmed_fields.contact_phone = True
        workflow.confirmed_fields.special_requests = True
        workflow.stage = WorkflowStage.SAVE_DATA
        workflow.saved_file_path = None
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
        topic_missing_field = _get_next_missing_field(workflow)
    else:
        workflow.stage = WorkflowStage.AWAIT_CONFIRMATION

    _sync_topic_with_stage(workflow, topic_missing_field)


def _handle_save_reservation(
    state: GlobalMemory, output: "SaveReservationOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow

    if output.follow_up_needed:
        workflow.stage = WorkflowStage.AWAIT_CONFIRMATION
    else:
        try:
            saved_path = save_reservation_snapshot(state)
            workflow.saved_file_path = str(saved_path)
        except Exception as exc:  # pragma: no cover - filesystem issue
            workflow.saved_file_path = f"save_failed: {exc}"
        workflow.stage = WorkflowStage.WRAP_UP
    _sync_topic_with_stage(workflow)


def _handle_alternative(
    state: GlobalMemory, output: "AlternativeProposalOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    topic_missing_field: Optional[str] = None

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
        topic_missing_field = _get_next_missing_field(workflow)
    else:
        workflow.availability_status = AvailabilityStatus.ALTERNATIVES_OFFERED
        if output.should_end_conversation:
            workflow.stage = WorkflowStage.END
        else:
            workflow.stage = WorkflowStage.AWAIT_AVAILABILITY

    _sync_topic_with_stage(workflow, topic_missing_field)


def _handle_error_recovery(state: GlobalMemory, output: "ErrorRecoveryOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.workflow.stage = output.reset_stage
    state.workflow.blocking_issue = None
    state.workflow.confirmation_status = ConfirmationStatus.PENDING
    next_missing = None
    if state.workflow.stage == WorkflowStage.PROVIDE_CONTACT:
        next_missing = _get_next_missing_field(state.workflow)
    _sync_topic_with_stage(state.workflow, next_missing)


_HANDLERS: Dict[SkillName, UpdateHandler] = {
    SkillName.GREETING: _handle_greeting,
    SkillName.AVAILABILITY: _handle_availability,
    SkillName.DETAILS_COLLECTION: _handle_details,
    SkillName.MENU_DISCUSSION: _handle_menu,
    SkillName.CONFIRMATION: _handle_confirmation,
    SkillName.ALTERNATIVE: _handle_alternative,
    SkillName.ERROR_RECOVERY: _handle_error_recovery,
    SkillName.SAVE_RESERVATION: _handle_save_reservation,
}
