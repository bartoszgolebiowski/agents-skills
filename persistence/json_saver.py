"""Utilities for persisting reservation data as JSON files."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from memory.models import GlobalMemory, ReservationDetails

_RESERVATION_DIR = Path(__file__).resolve().parent.parent / "reservations"


def _ensure_output_dir() -> Path:
    _RESERVATION_DIR.mkdir(parents=True, exist_ok=True)
    return _RESERVATION_DIR


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "reservation"


def _serialize_reservation(details: ReservationDetails) -> Dict[str, Any]:
    return {
        "date": details.date.isoformat() if details.date else None,
        "time": details.time.isoformat(timespec="minutes") if details.time else None,
        "party_size": details.party_size,
        "occasion": details.occasion,
        "special_requests": details.special_requests,
        "contact_name": details.contact_name,
        "contact_phone": details.contact_phone,
    }


def save_reservation_snapshot(state: GlobalMemory) -> Path:
    """Persist the reservation summary to disk and return the file path."""

    output_dir = _ensure_output_dir()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    guest_slug = _slugify(state.semantic.guest_name)
    filename = f"{guest_slug}_{timestamp}.json"
    file_path = output_dir / filename

    payload = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "guest": {
            "name": state.semantic.guest_name,
            "phone": state.semantic.guest_phone,
        },
        "restaurant": state.semantic.restaurant_name,
        "workflow": {
            "stage": state.workflow.stage,
            "availability_status": state.workflow.availability_status,
            "confirmation_status": state.workflow.confirmation_status,
            "selected_slot_note": state.workflow.selected_slot_note,
        },
        "goal_reservation": _serialize_reservation(state.working.goal_reservation),
        "confirmed_reservation": _serialize_reservation(
            state.working.confirmed_reservation
        ),
        "menu_preferences": {
            "requested": state.working.menu_preferences.requested,
            "highlights": state.working.menu_preferences.highlights,
            "dietary_notes": state.working.menu_preferences.dietary_notes,
        },
        "conversation_summary": {
            "turns": [
                {"speaker": turn.speaker, "message": turn.message}
                for turn in state.working.turns
            ],
        },
    }

    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return file_path
