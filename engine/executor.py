"""Executor agent responsible for LLM interactions."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from pydantic import BaseModel

from memory.models import GlobalMemory
from shared.enums import SkillName
from skills.registry import get_skill
from templates.environment import create_environment


class ExecutorAgent:
    """Executes a single skill by rendering its prompt and calling the LLM."""

    def __init__(self, llm_client: "LLMClientProtocol") -> None:
        self._llm_client = llm_client
        self._env = create_environment()

    def run(
        self, skill_name: SkillName, state: GlobalMemory, user_message: str
    ) -> BaseModel:
        """Execute a skill and return the structured output."""

        skill = get_skill(skill_name)
        context: Mapping[str, Any] = {
            "state": state,
            "user_message": user_message,
            "skill": skill,
        }
        prompt = skill.render_prompt(self._env, context)
        return self._llm_client.generate(
            prompt=prompt, response_model=skill.output_model, skill=skill, state=state
        )


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients used by the executor."""

    def generate(
        self, prompt: str, response_model: type[BaseModel], **kwargs: Any
    ) -> BaseModel: ...
