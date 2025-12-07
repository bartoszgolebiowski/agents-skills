"""High-level agent that coordinates the reservation workflow."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from engine.coordinator import CoordinatorAgent
from engine.executor import ExecutorAgent, LLMClientProtocol
from engine.llm import OpenRouterLLMClient
from memory.models import DesiredReservation, GlobalMemory, SemanticMemory
from memory.state_manager import (
    apply_skill_output,
    create_initial_state,
    record_user_turn,
)


class ReservationAgent:
    """Facade that exposes a simple conversational API."""

    def __init__(
        self,
        semantic_memory: SemanticMemory,
        desired_reservation: DesiredReservation,
        llm_client: Optional[LLMClientProtocol] = None,
    ) -> None:
        """Initialize the reservation agent.

        Args:
            semantic_memory: SemanticMemory with guest/restaurant data.
            desired_reservation: DesiredReservation with booking preferences.
            llm_client: Optional LLM client for generating responses.
        """
        self._state: GlobalMemory = create_initial_state(
            semantic_memory=semantic_memory, desired_reservation=desired_reservation
        )
        self._coordinator = CoordinatorAgent()
        client = llm_client or OpenRouterLLMClient()
        self._executor = ExecutorAgent(llm_client=client)

    @property
    def state(self) -> GlobalMemory:
        """Current immutable state snapshot."""

        return self._state

    def is_complete(self) -> bool:
        """Return True when the workflow reached a terminal stage."""

        return self._coordinator.select_skill(self._state) is None

    def step(self, user_message: Optional[str] = None) -> str:
        """Process an optional user message and return the agent reply."""

        if user_message:
            self._state = record_user_turn(self._state, user_message)

        skill_name = self._coordinator.select_skill(self._state)
        if skill_name is None:
            return "Rezerwacja została już zakończona."

        last_user_message = self._state.working.last_user_message or ""
        print(f"[DEBUG] State before: {self._state.model_dump_json()}")
        output = self._executor.run(skill_name, self._state, last_user_message)
        self._state = apply_skill_output(self._state, skill_name, output)
        print(f"[DEBUG] State after: {self._state.model_dump_json()}")
        return output.ai_response  # type: ignore

    def run_until_done(self) -> list[str]:
        """Execute skills until the workflow finishes (useful for demos/tests)."""

        responses: list[str] = []
        while True:
            skill_name = self._coordinator.select_skill(self._state)
            if skill_name is None:
                break
            last_user_message = self._state.working.last_user_message or ""
            output = self._executor.run(skill_name, self._state, last_user_message)
            self._state = apply_skill_output(self._state, skill_name, output)
            responses.append(output.ai_response)
        return responses
