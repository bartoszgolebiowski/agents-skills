"""LLM client implementations."""

from __future__ import annotations

import os
from typing import Any

import instructor
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from .executor import LLMClientProtocol

# Load .env once so OpenRouter credentials can be provided outside the shell.
load_dotenv()


class OpenRouterLLMClient(LLMClientProtocol):
    """LLM client that calls OpenRouter via the official OpenAI SDK."""

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Export it to use the live OpenRouter client."
            )

        self._model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self._temperature = (
            temperature
            if temperature is not None
            else float(os.getenv("OPENROUTER_TEMPERATURE", "0.2"))
        )
        self._max_output_tokens = (
            max_output_tokens
            if max_output_tokens is not None
            else int(os.getenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1200"))
        )
        raw_client = OpenAI(base_url=self.BASE_URL, api_key=key)
        self._client = instructor.patch(raw_client, mode=instructor.Mode.JSON)

    def generate(
        self, prompt: str, response_model: type[BaseModel], **_: Any
    ) -> BaseModel:
        return self._client.chat.completions.create(
            model=self._model,
            messages=self._prompt_to_messages(prompt),
            temperature=self._temperature,
            max_tokens=self._max_output_tokens,
            response_model=response_model,  # type: ignore
        )

    def _prompt_to_messages(self, prompt: str) -> list[dict[str, str]]:
        """Convert a raw prompt into chat messages format."""
        return [{"role": "system", "content": prompt}]
