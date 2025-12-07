"""Utility for creating a shared Jinja environment."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATES_PATH = Path(__file__).resolve().parent


def create_environment() -> Environment:
    """Return a configured Jinja2 environment for the agent templates."""

    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_PATH)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
