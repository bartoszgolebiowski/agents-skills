"""Immutable state management utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict

from pydantic import BaseModel

from memory.models import AlternativeOption, GlobalMemory, ReservationDetails
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


def create_initial_state() -> GlobalMemory:
    """Return a fully initialized memory tree for a new session."""

    state = GlobalMemory()
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
    state.workflow.awaiting_staff_reply = True
    state.working.pending_questions = []


def _handle_availability(
    state: GlobalMemory, output: "AvailabilitySkillOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    workflow.availability_status = output.availability_status
    workflow.selected_slot_note = output.selected_slot_note
    workflow.awaiting_staff_reply = False
    workflow.alternatives_pending = False
    workflow.blocking_issue = None
    state.working.pending_questions = output.pending_questions

    if output.suggested_alternatives:
        state.working.proposed_alternatives = [
            AlternativeOption(description=alt, accepted=False)
            for alt in output.suggested_alternatives
        ]
    elif output.availability_status == AvailabilityStatus.SLOT_ACCEPTED:
        state.working.proposed_alternatives = []

    if output.availability_status == AvailabilityStatus.SLOT_ACCEPTED:
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
    elif output.availability_status == AvailabilityStatus.WAITING_ON_STAFF:
        workflow.stage = WorkflowStage.AWAIT_AVAILABILITY
        workflow.awaiting_staff_reply = True
    elif output.availability_status == AvailabilityStatus.ALTERNATIVES_OFFERED:
        workflow.stage = WorkflowStage.REVIEW_ALTERNATIVES
        workflow.alternatives_pending = True
    elif output.availability_status == AvailabilityStatus.DECLINED:
        workflow.stage = WorkflowStage.REVIEW_ALTERNATIVES
        workflow.alternatives_pending = bool(output.suggested_alternatives)
    else:
        workflow.stage = WorkflowStage.SHARE_PREFERENCES


def _handle_details(state: GlobalMemory, output: "DetailsCollectionOutput") -> None:
    state.append_turn("agent", output.ai_response)
    details_payload = output.reservation_details or ReservationDetails()
    details_payload.contact_name = (
        details_payload.contact_name or state.semantic.guest_name
    )
    details_payload.contact_phone = (
        details_payload.contact_phone or state.semantic.guest_phone
    )
    state.working.shared_reservation = details_payload
    state.working.pending_questions = []
    workflow = state.workflow
    workflow.details_shared = all(
        [
            details_payload.date,
            details_payload.time,
            details_payload.party_size,
            details_payload.contact_name,
            details_payload.contact_phone,
        ]
    )
    workflow.menu_questions_pending = output.needs_menu_dialog
    if output.needs_menu_dialog:
        workflow.stage = WorkflowStage.MENU_DISCUSSION
        workflow.awaiting_staff_reply = False
    else:
        workflow.stage = WorkflowStage.AWAIT_CONFIRMATION
        workflow.awaiting_staff_reply = True


def _handle_menu(state: GlobalMemory, output: "MenuDiscussionOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.working.menu_preferences = output.menu_preferences
    workflow = state.workflow
    workflow.menu_questions_pending = output.next_stage == WorkflowStage.MENU_DISCUSSION
    workflow.stage = output.next_stage
    workflow.awaiting_staff_reply = (
        output.next_stage == WorkflowStage.AWAIT_CONFIRMATION
    )


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
        workflow.stage = WorkflowStage.WRAP_UP
        workflow.conversation_goal_met = True
        workflow.awaiting_staff_reply = False
        state.working.confirmed_reservation = output.confirmed_reservation
        state.working.pending_questions = []
    elif output.confirmation_status == ConfirmationStatus.NEEDS_CLARIFICATION:
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        workflow.awaiting_staff_reply = False
        state.working.pending_questions = (
            [output.error_message] if output.error_message else []
        )
        workflow.blocking_issue = None
    else:
        workflow.stage = WorkflowStage.AWAIT_CONFIRMATION
        workflow.awaiting_staff_reply = True


def _handle_alternative(
    state: GlobalMemory, output: "AlternativeProposalOutput"
) -> None:
    state.append_turn("agent", output.ai_response)
    workflow = state.workflow
    workflow.awaiting_staff_reply = False
    workflow.alternatives_pending = False

    if output.alternative_selected and output.accepted_slot_description:
        workflow.availability_status = AvailabilityStatus.SLOT_ACCEPTED
        workflow.alternatives_pending = False
        workflow.stage = WorkflowStage.PROVIDE_CONTACT
        workflow.selected_slot_note = output.accepted_slot_description
        state.working.proposed_alternatives = [
            AlternativeOption(
                description=output.accepted_slot_description,
                notes="accepted by guest",
                accepted=True,
            )
        ]
    else:
        workflow.availability_status = AvailabilityStatus.ALTERNATIVES_OFFERED
        if output.should_end_conversation:
            workflow.stage = WorkflowStage.END
        else:
            workflow.stage = WorkflowStage.AWAIT_AVAILABILITY
            workflow.awaiting_staff_reply = True


def _handle_error_recovery(state: GlobalMemory, output: "ErrorRecoveryOutput") -> None:
    state.append_turn("agent", output.ai_response)
    state.workflow.stage = output.reset_stage
    state.workflow.blocking_issue = None
    state.workflow.confirmation_status = ConfirmationStatus.PENDING
    state.workflow.awaiting_staff_reply = False


_HANDLERS: Dict[SkillName, UpdateHandler] = {
    SkillName.GREETING: _handle_greeting,
    SkillName.AVAILABILITY: _handle_availability,
    SkillName.DETAILS_COLLECTION: _handle_details,
    SkillName.MENU_DISCUSSION: _handle_menu,
    SkillName.CONFIRMATION: _handle_confirmation,
    SkillName.ALTERNATIVE: _handle_alternative,
    SkillName.ERROR_RECOVERY: _handle_error_recovery,
}
