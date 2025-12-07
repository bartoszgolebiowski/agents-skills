"""Base class for declarative skills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Type

from jinja2 import Environment
from pydantic import BaseModel

from shared.enums import SkillName


@dataclass(frozen=True, slots=True)
class Skill:
    """Declarative description of a single conversational capability."""

    name: SkillName
    template_path: str
    output_model: Type[BaseModel]
    description: str

    def render_prompt(self, env: Environment, context: Mapping[str, Any]) -> str:
        """Render the Jinja template with a supplied context."""

        template = env.get_template(self.template_path)
        return template.render(**context)
