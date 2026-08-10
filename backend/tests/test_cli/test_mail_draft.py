"""Tests for cli/mail_draft.py — verify it never sends and handles edge cases."""

import subprocess
from unittest.mock import patch

from cli.mail_draft import create_draft


def _kwargs(**overrides):
    base = dict(
        recipient="jane@acmedental.example.com",
        subject="Quick question about Acme Dental's scheduling",
        body="Hi Jane, ...",
        lead_id="ld_abc123",
        source_url="https://acmedental.example.com",
    )
    base.update(overrides)
    return base


class TestCreateDraft:
    def test_missing_recipient_returns_needs_input(self):
        result = create_draft(**_kwargs(recipient=""))
        assert result.status == "needs_input"

    def test_non_macos_returns_manual_required(self):
        with patch("cli.mail_draft.platform.system", return_value="Linux"):
            result = create_draft(**_kwargs())
        assert result.status == "manual_required"
        assert "macOS" in result.reason

    def test_never_calls_send(self):
        """The AppleScript passed to osascript must not contain a send command."""
        captured = {}

        def fake_run(args, **kwargs):
            captured["args"] = args
            return subprocess.CompletedProcess(args, 0)

        with patch("cli.mail_draft.platform.system", return_value="Darwin"):
            with patch("cli.mail_draft.subprocess.run", side_effect=fake_run):
                result = create_draft(**_kwargs())

        assert result.status == "created"
        script_text = " ".join(captured["args"])
        assert "send newDraft" not in script_text
        assert "make new outgoing message" in script_text
        assert "save newDraft" in script_text

    def test_includes_lead_id_and_source_in_body(self):
        with patch("cli.mail_draft.platform.system", return_value="Darwin"):
            with patch("cli.mail_draft.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)
                create_draft(**_kwargs())

        script_text = " ".join(mock_run.call_args.args[0])
        assert "ld_abc123" in script_text
        assert "acmedental.example.com" in script_text

    def test_automation_failure_returns_manual_required(self):
        with patch("cli.mail_draft.platform.system", return_value="Darwin"):
            with patch(
                "cli.mail_draft.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "osascript", stderr="not authorized"),
            ):
                result = create_draft(**_kwargs())
        assert result.status == "manual_required"
        assert "not authorized" in result.reason

    def test_escapes_quotes_in_subject(self):
        with patch("cli.mail_draft.platform.system", return_value="Darwin"):
            with patch("cli.mail_draft.subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess([], 0)
                create_draft(**_kwargs(subject='Say "hello"'))

        script_text = " ".join(mock_run.call_args.args[0])
        assert '\\"hello\\"' in script_text
