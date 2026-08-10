"""Browser-assisted lead verification.

Minimal version: opens each of a lead's URLs (source/company site, social
profiles) in the user's default browser via the stdlib `webbrowser` module,
and records a verified/rejected note locally via cli.state.

This is intentionally not wired to a specific automation library — the goal
is a working baseline today. See README Roadmap for a future Codex
Chrome / Playwright / browser-use-driven version that can navigate and
extract confirmation evidence automatically.
"""

from __future__ import annotations

import webbrowser
from typing import Any

from cli import state


def urls_for_lead(lead: dict[str, Any]) -> list[str]:
    """Return every URL worth opening to verify a lead: source, website, socials."""
    urls: list[str] = []
    for key in ("source_url", "website"):
        url = str(lead.get(key) or "").strip()
        if url and url not in urls:
            urls.append(url)
    for url in lead.get("evidence") or []:
        if url and url not in urls:
            urls.append(url)
    return urls


def open_lead(lead: dict[str, Any]) -> list[str]:
    """Open every URL for a lead in the default browser. Returns the URLs opened."""
    urls = urls_for_lead(lead)
    for url in urls:
        webbrowser.open(url)
    return urls


def record_verification(lead_id: str, status: str, note: str) -> dict[str, Any]:
    if status not in ("verified", "rejected"):
        raise ValueError("status must be 'verified' or 'rejected'")
    return state.record_verification(lead_id, status, note)
