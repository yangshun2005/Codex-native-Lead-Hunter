"""macOS Mail.app draft creation — draft only, never sends.

Uses AppleScript (via osascript) to create an outgoing message in Mail.app
and save it as a draft. There is no "send" step anywhere in this module —
sending a drafted email is a deliberate, manual action the user takes in
Mail.app themselves. See SAFETY.md.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field
from typing import Literal

Status = Literal["created", "needs_input", "manual_required"]


@dataclass
class MailDraftResult:
    status: Status
    reason: str = ""
    summary: dict = field(default_factory=dict)


def _escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _footer(lead_id: str, source_url: str) -> str:
    lines = ["", "---"]
    if lead_id:
        lines.append(f"Lead ID: {lead_id}")
    if source_url:
        lines.append(f"Source: {source_url}")
    return "\n".join(lines)


def build_confirmation_summary(
    *, recipient: str, subject: str, body: str, lead_id: str, source_url: str
) -> dict:
    return {
        "recipient": recipient,
        "subject": subject,
        "body_preview": (body[:200] + "…") if len(body) > 200 else body,
        "lead_id": lead_id,
        "source_url": source_url,
        "action": (
            "Will create a Mail.app DRAFT only. Nothing is sent. "
            "You must open Mail.app and click Send yourself."
        ),
    }


def create_draft(
    *,
    recipient: str,
    subject: str,
    body: str,
    lead_id: str,
    source_url: str,
) -> MailDraftResult:
    """Create a Mail.app draft. Returns a result with status:

    - "created": draft was created in Mail.app (not sent).
    - "needs_input": required field (recipient) missing — caller must supply it.
    - "manual_required": Mail.app isn't available/scriptable here (non-macOS,
      Mail.app not set up, or Automation permission not granted) — the caller
      should write the email manually.
    """
    summary = build_confirmation_summary(
        recipient=recipient, subject=subject, body=body, lead_id=lead_id, source_url=source_url
    )

    if not recipient or not recipient.strip():
        return MailDraftResult(
            status="needs_input", reason="Lead has no recipient email address.", summary=summary
        )

    if platform.system() != "Darwin":
        return MailDraftResult(
            status="manual_required",
            reason="Mail.app drafts are only supported on macOS. Write this email manually.",
            summary=summary,
        )

    full_body = f"{body}{_footer(lead_id, source_url)}"
    escaped_subject = _escape_applescript(subject)
    escaped_body = _escape_applescript(full_body)
    escaped_recipient = _escape_applescript(recipient)
    script_lines = [
        'tell application "Mail"',
        "set newDraft to make new outgoing message with properties "
        f'{{subject:"{escaped_subject}", content:"{escaped_body}", visible:true}}',
        "tell newDraft",
        "make new to recipient at end of to recipients with properties "
        f'{{address:"{escaped_recipient}"}}',
        "end tell",
        "save newDraft",
        "end tell",
    ]
    args = ["osascript"]
    for line in script_lines:
        args += ["-e", line]

    try:
        subprocess.run(args, check=True, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return MailDraftResult(
            status="manual_required",
            reason="osascript not found — Mail.app drafts require macOS.",
            summary=summary,
        )
    except subprocess.CalledProcessError as exc:
        return MailDraftResult(
            status="manual_required",
            reason=f"Mail.app automation failed ({exc.stderr.strip() or exc}). "
            "Check System Settings > Privacy & Security > Automation permissions "
            "for your terminal/Codex app.",
            summary=summary,
        )
    except subprocess.TimeoutExpired:
        return MailDraftResult(
            status="manual_required", reason="Mail.app did not respond in time.", summary=summary
        )

    return MailDraftResult(
        status="created",
        reason="Draft created in Mail.app. Review and send it yourself.",
        summary=summary,
    )
