"""Pydantic models that define every memory layer of the agent."""

from __future__ import annotations

from datetime import date as dt_date, time as dt_time, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.enums import (
    AvailabilityStatus,
    ConfirmationStatus,
    DiscussionTopic,
    WorkflowStage,
)


class ConversationTurn(BaseModel):
    """Represents a single entry in the short-term transcript."""

    speaker: str
    message: str


class ReservationDetails(BaseModel):
    """Structured information that is required to book a table."""

    date: Optional[dt_date] = None
    time: Optional[dt_time] = None
    party_size: Optional[int] = Field(default=None, ge=1, le=16)
    occasion: Optional[str] = None
    special_requests: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class MenuPreferences(BaseModel):
    """Captures optional menu discussion outcomes."""

    requested: bool = False
    highlights: List[str] = Field(default_factory=list)
    dietary_notes: Optional[str] = None


class AlternativeOption(BaseModel):
    """A candidate slot suggested by the staff when no tables are available."""

    description: str
    notes: Optional[str] = None
    accepted: bool = False


class CoreMemory(BaseModel):
    """Static identity and guardrails for the guest persona."""

    agent_name: str = "Sarah"
    persona: str = (
        "You are Sarah Mitchell, a thoughtful person who wants to book a table at Azure Bistro. "
        "Always speak as a guest (never as staff), share only personal data from memory, and "
        "respond with gratitude even when availability is limited. Keep your responses to maximum two "
        "concise sentences and reveal only details that are currently being asked by staff."
    )
    languages: List[str] = Field(default_factory=lambda: ["en"])
    core_principles: List[str] = Field(
        default_factory=lambda: [
            "Always speak as a guest and never pretend to be staff.",
            "Thank them for every response and show patience.",
            "Do not make up new contact information.",
            "Ask for clarification instead of guessing when you don't know something.",
            "Respond in maximum two sentences and only within the scope of what is being asked.",
        ]
    )


class DesiredReservation(BaseModel):
    """Preferred booking parameters the guest would like to request."""

    date: dt_date = Field(default_factory=lambda: dt_date.today() + timedelta(days=1))
    time: dt_time = dt_time(hour=19, minute=0)
    party_size: int = 2
    occasion: Optional[str] = ""
    special_requests: Optional[str] = ""


class SemanticMemory(BaseModel):
    """Long-term knowledge the guest relies on."""

    restaurant_name: str = ""
    guest_name: str = ""
    guest_phone: str = ""
    celebration_reason: str = ""
    favorite_dishes: List[str] = Field(default_factory=lambda: [])
    dietary_notes: Optional[str] = ""
    talking_points: List[str] = Field(default_factory=lambda: [])
    desired_reservation: DesiredReservation = Field(default_factory=DesiredReservation)
    fallback_slots: List[str] = Field(default_factory=lambda: [])

    @classmethod
    def create(
        cls,
        restaurant_name: str = "",
        guest_name: str = "",
        guest_phone: str = "",
        celebration_reason: str = "",
        favorite_dishes: Optional[List[str]] = None,
        dietary_notes: Optional[str] = "",
        talking_points: Optional[List[str]] = None,
        desired_reservation: Optional[DesiredReservation] = None,
        fallback_slots: Optional[List[str]] = None,
    ) -> SemanticMemory:
        """Factory method to create SemanticMemory with custom values."""
        return cls(
            restaurant_name=restaurant_name,
            guest_name=guest_name,
            guest_phone=guest_phone,
            celebration_reason=celebration_reason,
            favorite_dishes=favorite_dishes or [],
            dietary_notes=dietary_notes,
            talking_points=talking_points or [],
            desired_reservation=desired_reservation or DesiredReservation(),
            fallback_slots=fallback_slots or [],
        )


class EpisodicMemory(BaseModel):
    """Log of important learning moments."""

    events: List[str] = Field(default_factory=list)


class ConfirmedFields(BaseModel):
    """Tracks which reservation fields have been explicitly confirmed by staff."""

    date: bool = False
    time: bool = False
    party_size: bool = False
    occasion: bool = False
    special_requests: bool = False
    contact_name: bool = False
    contact_phone: bool = False

    def all_required_confirmed(self) -> bool:
        """Check if all fields (date, time, party_size, occasion, special_requests, contact_name, contact_phone) are confirmed."""
        return all(
            [
                self.date,
                self.time,
                self.party_size,
                self.occasion,
                self.special_requests,
                self.contact_name,
                self.contact_phone,
            ]
        )


class WorkflowMemory(BaseModel):
    """Guest-centric state flags that drive the coordinator."""

    stage: WorkflowStage = WorkflowStage.INTRO
    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    confirmation_status: ConfirmationStatus = ConfirmationStatus.PENDING
    confirmed_fields: ConfirmedFields = Field(default_factory=ConfirmedFields)
    missing_explicit_confirmations: List[str] = Field(default_factory=list)
    blocking_issue: Optional[str] = None
    selected_slot_note: Optional[str] = None
    saved_file_path: Optional[str] = None
    current_topic: DiscussionTopic = DiscussionTopic.NONE


class WorkingMemory(BaseModel):
    """Short-term scratchpad for the current dialogue."""

    turns: List[ConversationTurn] = Field(default_factory=list)
    last_user_message: Optional[str] = None
    last_ai_message: Optional[str] = None
    goal_reservation: ReservationDetails = Field(default_factory=ReservationDetails)
    confirmed_reservation: ReservationDetails = Field(
        default_factory=ReservationDetails
    )
    menu_preferences: MenuPreferences = Field(default_factory=MenuPreferences)
    proposed_alternatives: List[AlternativeOption] = Field(default_factory=list)
    pending_questions: List[str] = Field(default_factory=list)


class GlobalMemory(BaseModel):
    """Container that aggregates every memory layer."""

    core: CoreMemory = Field(default_factory=CoreMemory)
    semantic: SemanticMemory = Field(default_factory=SemanticMemory)
    episodic: EpisodicMemory = Field(default_factory=EpisodicMemory)
    workflow: WorkflowMemory = Field(default_factory=WorkflowMemory)
    working: WorkingMemory = Field(default_factory=WorkingMemory)

    def append_turn(self, speaker: str, message: str) -> None:
        """Append a conversation turn to working memory."""

        self.working.turns.append(ConversationTurn(speaker=speaker, message=message))
        if speaker == "user":
            self.working.last_user_message = message
        else:
            self.working.last_ai_message = message
