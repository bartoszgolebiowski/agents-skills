"""Deterministic routing logic for the reservation workflow."""

from __future__ import annotations

from typing import Optional

from memory.models import GlobalMemory
from shared.enums import ConfirmationStatus, SkillName, WorkflowStage


class CoordinatorAgent:
    """Pure state machine that selects the next skill to execute."""

    terminal_stages = {WorkflowStage.WRAP_UP, WorkflowStage.END}

    def select_skill(self, state: GlobalMemory) -> Optional[SkillName]:
        """Return the appropriate skill for the current workflow stage."""

        workflow = state.workflow

        if workflow.stage in self.terminal_stages:
            return None

        if workflow.blocking_issue:
            return SkillName.ERROR_RECOVERY

        if workflow.stage == WorkflowStage.INTRO:
            return SkillName.GREETING

        if workflow.stage in {
            WorkflowStage.SHARE_PREFERENCES,
            WorkflowStage.AWAIT_AVAILABILITY,
        }:
            return SkillName.AVAILABILITY

        if workflow.stage == WorkflowStage.REVIEW_ALTERNATIVES:
            return SkillName.ALTERNATIVE

        if workflow.stage == WorkflowStage.PROVIDE_CONTACT:
            return SkillName.DETAILS_COLLECTION

        if workflow.stage == WorkflowStage.MENU_DISCUSSION:
            return SkillName.MENU_DISCUSSION

        if workflow.stage == WorkflowStage.AWAIT_CONFIRMATION:
            if workflow.confirmation_status == ConfirmationStatus.NEEDS_CLARIFICATION:
                return SkillName.DETAILS_COLLECTION
            return SkillName.CONFIRMATION

        if workflow.stage == WorkflowStage.SAVE_DATA:
            return SkillName.SAVE_RESERVATION

        # Default fallback ensures we never get stuck.
        return SkillName.GREETING
