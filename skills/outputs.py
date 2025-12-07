"""Structured outputs produced by each skill."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from memory.models import MenuPreferences, ReservationDetails
from shared.enums import AvailabilityStatus, ConfirmationStatus, WorkflowStage


class SkillOutput(BaseModel):
    """Base class for every structured response."""

    ai_response: str


class GreetingSkillOutput(SkillOutput):
    """Greeting responses do not need extra structure."""


class AvailabilitySkillOutput(SkillOutput):
    """Captures how the staff responded to the requested slot."""

    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    suggested_alternatives: List[str] = Field(default_factory=list)
    selected_slot_note: Optional[str] = None
    pending_questions: List[str] = Field(default_factory=list)
    special_request_rejected: bool = False


class DetailsCollectionOutput(SkillOutput):
    """Collects information required for a booking."""

    reservation_details: ReservationDetails = Field(default_factory=ReservationDetails)
    needs_menu_dialog: bool = False


class MenuDiscussionOutput(SkillOutput):
    """Captures menu-related questions or highlights."""

    menu_preferences: MenuPreferences = Field(default_factory=MenuPreferences)
    next_stage: WorkflowStage = WorkflowStage.AWAIT_CONFIRMATION


class ConfirmationSkillOutput(SkillOutput):
    """Represents the outcome of the booking confirmation."""

    confirmation_status: ConfirmationStatus = ConfirmationStatus.PENDING
    booking_reference: Optional[str] = None
    error_message: Optional[str] = None
    confirmed_reservation: ReservationDetails = Field(
        default_factory=ReservationDetails
    )


class AlternativeProposalOutput(SkillOutput):
    """Used when proposing or negotiating alternative options."""

    alternative_selected: bool = False
    accepted_slot_description: Optional[str] = None
    should_end_conversation: bool = False


class ErrorRecoveryOutput(SkillOutput):
    """Guides the state machine back to a safe point after failures."""

    reset_stage: WorkflowStage = WorkflowStage.SHARE_PREFERENCES


class SaveReservationOutput(SkillOutput):
    """Final acknowledgement once reservation details are stored."""

    follow_up_needed: bool = False
