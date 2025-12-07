"""Pydantic models that define every memory layer of the agent."""

from __future__ import annotations

from datetime import date as dt_date, time as dt_time, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.enums import AvailabilityStatus, ConfirmationStatus, WorkflowStage


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

    agent_name: str = "Klara"
    persona: str = (
        "Jesteś Klarą Nowak, troskliwą osobą, która chce zarezerwować stolik w Atut Bistro"
        "Zawsze wypowiadasz się jako gość (nigdy jako personel), udostępniasz jedynie dane osobowe w pamięci i"
        "odpowiadasz z wdzięcznością, nawet gdy dostępność jest ograniczona. Ogranicz swoje odpowiedzi do maksymalnie dwóch"
        "zwięzłych zdań i ujawniaj tylko te szczegóły, o które aktualnie pyta personel"
    )
    languages: List[str] = Field(default_factory=lambda: ["pl", "en"])
    core_principles: List[str] = Field(
        default_factory=lambda: [
            "Zawsze mów jako gość i nie udawaj obsługi.",
            "Dziękuj za każdą odpowiedź i okazuj cierpliwość.",
            "Nie wymyślaj nowych danych kontaktowych.",
            "Proś o doprecyzowanie zamiast zgadywać, gdy czegoś nie wiesz.",
            "Odpowiadaj maksymalnie w dwóch zdaniach i tylko w zakresie informacji, o które proszą.",
        ]
    )


class DesiredReservation(BaseModel):
    """Preferred booking parameters the guest would like to request."""

    date: dt_date = Field(default_factory=lambda: dt_date.today() + timedelta(days=1))
    time: dt_time = dt_time(hour=19, minute=0)
    party_size: int = 2
    occasion: Optional[str] = "kolacja"
    special_requests: Optional[str] = "stolik blisko okna"


class SemanticMemory(BaseModel):
    """Long-term knowledge the guest relies on."""

    restaurant_name: str = "Atut Bistro"
    guest_name: str = "Klara Nowak"
    guest_phone: str = "+48123123123"
    celebration_reason: str = "rocznica"
    favorite_dishes: List[str] = Field(
        default_factory=lambda: [
            "Tatar z łososia",
            "Risotto z kurkami",
            "Suflet czekoladowy",
        ]
    )
    dietary_notes: Optional[str] = "bez laktozy"
    talking_points: List[str] = Field(
        default_factory=lambda: [
            "Uwielbiam kameralny ogródek Atut Bistro.",
            "Słyszałam rewelacje o autorskim menu degustacyjnym.",
        ]
    )
    desired_reservation: DesiredReservation = Field(default_factory=DesiredReservation)
    fallback_slots: List[str] = Field(
        default_factory=lambda: [
            "jutro 18:00",
            "jutro 20:30",
            "za dwa dni 19:00",
        ]
    )


class EpisodicMemory(BaseModel):
    """Log of important learning moments."""

    events: List[str] = Field(default_factory=list)


class WorkflowMemory(BaseModel):
    """Guest-centric state flags that drive the coordinator."""

    stage: WorkflowStage = WorkflowStage.INTRO
    availability_status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    confirmation_status: ConfirmationStatus = ConfirmationStatus.PENDING
    details_shared: bool = False
    blocking_issue: Optional[str] = None
    selected_slot_note: Optional[str] = None


class WorkingMemory(BaseModel):
    """Short-term scratchpad for the current dialogue."""

    turns: List[ConversationTurn] = Field(default_factory=list)
    last_user_message: Optional[str] = None
    last_ai_message: Optional[str] = None
    goal_reservation: ReservationDetails = Field(default_factory=ReservationDetails)
    shared_reservation: ReservationDetails = Field(default_factory=ReservationDetails)
    confirmed_reservation: ReservationDetails = Field(
        default_factory=ReservationDetails
    )
    staff_feedback: Optional[str] = None
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
            self.working.staff_feedback = message
        else:
            self.working.last_ai_message = message
