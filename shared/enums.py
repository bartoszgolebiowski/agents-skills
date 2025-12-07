"""Shared enumerations used across the agent layers."""

from __future__ import annotations

from enum import Enum


class WorkflowStage(str, Enum):
    """Deterministic stages of the reservation flow from the guest's POV."""

    INTRO = "intro"
    SHARE_PREFERENCES = "share_preferences"
    AWAIT_AVAILABILITY = "await_availability"
    REVIEW_ALTERNATIVES = "review_alternatives"
    PROVIDE_CONTACT = "provide_contact"
    MENU_DISCUSSION = "menu_discussion"
    AWAIT_CONFIRMATION = "await_confirmation"
    WRAP_UP = "wrap_up"
    END = "end"


class AvailabilityStatus(str, Enum):
    """Represents how the restaurant responded to the requested slot."""

    UNKNOWN = "unknown"
    WAITING_ON_STAFF = "waiting_on_staff"
    SLOT_ACCEPTED = "slot_accepted"
    ALTERNATIVES_OFFERED = "alternatives_offered"
    DECLINED = "declined"


class ConfirmationStatus(str, Enum):
    """Describes the state of the staff's confirmation attempt."""

    PENDING = "pending"
    CONFIRMED_BY_STAFF = "confirmed_by_staff"
    NEEDS_CLARIFICATION = "needs_clarification"


class SkillName(str, Enum):
    """Identifiers for each declarative skill."""

    GREETING = "skill.greeting"
    AVAILABILITY = "skill.availability"
    DETAILS_COLLECTION = "skill.details"
    MENU_DISCUSSION = "skill.menu"
    CONFIRMATION = "skill.confirmation"
    ALTERNATIVE = "skill.alternative"
    ERROR_RECOVERY = "skill.error_recovery"
