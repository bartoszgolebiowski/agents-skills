"""Skill registry for the reservation agent."""

from __future__ import annotations

from typing import Dict

from skills.base import Skill
from skills import outputs
from shared.enums import SkillName

_SKILLS: Dict[SkillName, Skill] = {
    SkillName.GREETING: Skill(
        name=SkillName.GREETING,
        template_path="skills/greeting.j2",
        output_model=outputs.GreetingSkillOutput,
        description="Greet the staff and state the intent to book a table.",
    ),
    SkillName.AVAILABILITY: Skill(
        name=SkillName.AVAILABILITY,
        template_path="skills/availability.j2",
        output_model=outputs.AvailabilitySkillOutput,
        description="Share desired slot details and interpret staff availability responses.",
    ),
    SkillName.DETAILS_COLLECTION: Skill(
        name=SkillName.DETAILS_COLLECTION,
        template_path="skills/details.j2",
        output_model=outputs.DetailsCollectionOutput,
        description="Provide the guest's booking metadata and confirm next steps.",
    ),
    SkillName.MENU_DISCUSSION: Skill(
        name=SkillName.MENU_DISCUSSION,
        template_path="skills/menu.j2",
        output_model=outputs.MenuDiscussionOutput,
        description="Ask the staff follow-up questions about the menu.",
    ),
    SkillName.CONFIRMATION: Skill(
        name=SkillName.CONFIRMATION,
        template_path="skills/confirmation.j2",
        output_model=outputs.ConfirmationSkillOutput,
        description="Interpret the staff's final answer and react as the guest.",
    ),
    SkillName.ALTERNATIVE: Skill(
        name=SkillName.ALTERNATIVE,
        template_path="skills/alternative.j2",
        output_model=outputs.AlternativeProposalOutput,
        description="Evaluate and respond to alternative slots suggested by the staff.",
    ),
    SkillName.ERROR_RECOVERY: Skill(
        name=SkillName.ERROR_RECOVERY,
        template_path="skills/error_recovery.j2",
        output_model=outputs.ErrorRecoveryOutput,
        description="Recover from booking errors and restart the request if needed.",
    ),
}


def get_skill(skill_name: SkillName) -> Skill:
    """Return the requested skill definition."""

    return _SKILLS[skill_name]


def all_skills() -> Dict[SkillName, Skill]:
    """Expose the internal registry for inspection/testing."""

    return _SKILLS.copy()
