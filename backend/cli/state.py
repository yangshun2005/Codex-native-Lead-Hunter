"""Local CLI state — remembers the last hunt you ran and lead verification notes.

Stored under ./.lead_hunter/ in the current working directory (gitignored),
never sent anywhere. This is purely a convenience so `lead-hunter leads list`
doesn't require re-passing --hunt-id every time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_STATE_DIR = Path(".lead_hunter")
_STATE_FILE = _STATE_DIR / "state.json"
_VERIFICATIONS_FILE = _STATE_DIR / "verifications.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def set_current_hunt(hunt_id: str) -> None:
    state = _read_json(_STATE_FILE)
    state["current_hunt_id"] = hunt_id
    _write_json(_STATE_FILE, state)


def get_current_hunt() -> str | None:
    return _read_json(_STATE_FILE).get("current_hunt_id")


def record_verification(lead_id: str, status: str, note: str) -> dict[str, Any]:
    from datetime import datetime, timezone

    verifications = _read_json(_VERIFICATIONS_FILE)
    entry = {"status": status, "note": note, "verified_at": datetime.now(timezone.utc).isoformat()}
    verifications[lead_id] = entry
    _write_json(_VERIFICATIONS_FILE, verifications)
    return entry


def get_verification(lead_id: str) -> dict[str, Any] | None:
    return _read_json(_VERIFICATIONS_FILE).get(lead_id)


def all_verifications() -> dict[str, Any]:
    return _read_json(_VERIFICATIONS_FILE)
