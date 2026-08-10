"""Tests for cli/browser_verify.py."""

from unittest.mock import patch

import pytest

from cli import browser_verify


def _lead(**overrides):
    base = {
        "source_url": "https://acmedental.example.com",
        "website": "https://acmedental.example.com",
        "evidence": ["https://acmedental.example.com", "https://linkedin.com/company/acme-dental"],
    }
    base.update(overrides)
    return base


class TestUrlsForLead:
    def test_dedupes_source_and_website(self):
        urls = browser_verify.urls_for_lead(_lead())
        assert urls.count("https://acmedental.example.com") == 1

    def test_includes_evidence_links(self):
        urls = browser_verify.urls_for_lead(_lead())
        assert "https://linkedin.com/company/acme-dental" in urls

    def test_handles_missing_fields(self):
        assert browser_verify.urls_for_lead({}) == []


class TestOpenLead:
    def test_opens_every_url(self):
        with patch("cli.browser_verify.webbrowser.open") as mock_open:
            opened = browser_verify.open_lead(_lead())
        assert mock_open.call_count == len(opened)
        mock_open.assert_any_call("https://acmedental.example.com")
        mock_open.assert_any_call("https://linkedin.com/company/acme-dental")


class TestRecordVerification:
    def test_rejects_invalid_status(self):
        with pytest.raises(ValueError):
            browser_verify.record_verification("ld_abc", "maybe", "")

    def test_records_verified(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        entry = browser_verify.record_verification("ld_abc", "verified", "looks legit")
        assert entry["status"] == "verified"
        assert entry["note"] == "looks legit"
