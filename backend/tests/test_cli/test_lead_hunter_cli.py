"""Tests for cli/lead_hunter.py — the CLI entry point.

Mocks ApiClient network calls; never hits a real server.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from cli import lead_hunter


def _hunt_result():
    return {
        "hunt_id": "hunt-1",
        "status": "completed",
        "leads": [
            {
                "company_name": "Acme Dental",
                "website": "https://acmedental.example.com",
                "industry": "Dental",
                "emails": ["jane@acmedental.example.com"],
                "phone_numbers": [],
                "social_media": {},
                "contact_person": "Jane Doe",
                "country_code": "US",
                "source_keyword": "dentists in California",
                "match_score": 0.9,
            },
            {
                "company_name": "LowFit Co",
                "website": "https://lowfit.example.com",
                "industry": "Other",
                "emails": [],
                "phone_numbers": [],
                "social_media": {},
                "contact_person": None,
                "country_code": "US",
                "source_keyword": "",
                "match_score": 0.1,
            },
        ],
        "email_sequences": [],
    }


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


class TestLeadsList:
    def test_lists_all_leads_as_json(self, capsys):
        with patch.object(lead_hunter.ApiClient, "list_hunts", return_value=[{"hunt_id": "hunt-1"}]):
            with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=_hunt_result()):
                lead_hunter.main(["leads", "list", "--json"])

        output = json.loads(capsys.readouterr().out)
        assert output["hunt_id"] == "hunt-1"
        assert len(output["leads"]) == 2

    def test_filters_by_min_fit_score(self, capsys):
        with patch.object(lead_hunter.ApiClient, "list_hunts", return_value=[{"hunt_id": "hunt-1"}]):
            with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=_hunt_result()):
                lead_hunter.main(["leads", "list", "--json", "--min-fit-score", "7"])

        output = json.loads(capsys.readouterr().out)
        assert len(output["leads"]) == 1
        assert output["leads"][0]["company"] == "Acme Dental"

    def test_uses_explicit_hunt_id_without_calling_list_hunts(self, capsys):
        with patch.object(lead_hunter.ApiClient, "list_hunts") as mock_list:
            with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=_hunt_result()):
                lead_hunter.main(["leads", "list", "--hunt-id", "hunt-1", "--json"])
        mock_list.assert_not_called()


class TestLeadInspect:
    def test_inspect_known_lead(self, capsys):
        with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=_hunt_result()):
            lead_hunter.main(["lead", "inspect", lead_hunter.compute_lead_id(_hunt_result()["leads"][0]), "--hunt-id", "hunt-1"])
        output = json.loads(capsys.readouterr().out)
        assert output["company"] == "Acme Dental"
        assert output["fit_score"] == 9

    def test_inspect_unknown_lead_exits(self):
        with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=_hunt_result()):
            with pytest.raises(SystemExit):
                lead_hunter.main(["lead", "inspect", "ld_doesnotexist", "--hunt-id", "hunt-1"])


class TestVerify:
    def test_records_verification(self, capsys):
        lead_hunter.main(["verify", "ld_abc", "--status", "verified", "--note", "checked linkedin"])
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "verified"
        assert output["note"] == "checked linkedin"

    def test_invalid_status_rejected_by_argparse(self):
        with pytest.raises(SystemExit):
            lead_hunter.main(["verify", "ld_abc", "--status", "maybe"])


class TestExport:
    def test_writes_csv(self, tmp_path):
        out_file = tmp_path / "out.csv"
        with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=_hunt_result()):
            lead_hunter.main(["export", "--hunt-id", "hunt-1", "--out", str(out_file)])
        content = out_file.read_text()
        assert "Acme Dental" in content
        assert "LowFit Co" in content


class TestMailDraft:
    def test_needs_input_when_no_email(self, capsys):
        result = _hunt_result()
        no_email_lead = result["leads"][1]
        lead_id = lead_hunter.compute_lead_id(no_email_lead)
        with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=result):
            with patch("cli.lead_hunter.draft.generate_draft", return_value={"subject": "s", "body": "b", "source": "generated"}):
                with pytest.raises(SystemExit) as exc_info:
                    lead_hunter.main(["mail-draft", lead_id, "--hunt-id", "hunt-1"])
        assert exc_info.value.code == 2
        out = capsys.readouterr().out
        assert "needs_input" in out

    def test_created_draft_with_explicit_subject_body(self, capsys):
        result = _hunt_result()
        lead_id = lead_hunter.compute_lead_id(result["leads"][0])
        with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=result):
            with patch("cli.lead_hunter.create_draft") as mock_create:
                mock_create.return_value = MagicMock(status="created", reason="ok")
                lead_hunter.main(
                    ["mail-draft", lead_id, "--hunt-id", "hunt-1", "--subject", "Hi", "--body", "Body text"]
                )
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        assert kwargs["subject"] == "Hi"
        assert kwargs["body"] == "Body text"
        assert kwargs["recipient"] == "jane@acmedental.example.com"


class TestOpen:
    def test_opens_lead_urls(self, capsys):
        result = _hunt_result()
        lead_id = lead_hunter.compute_lead_id(result["leads"][0])
        with patch.object(lead_hunter.ApiClient, "get_hunt_result", return_value=result):
            with patch("cli.lead_hunter.browser_verify.webbrowser.open") as mock_open:
                lead_hunter.main(["open", lead_id, "--hunt-id", "hunt-1"])
        assert mock_open.called
