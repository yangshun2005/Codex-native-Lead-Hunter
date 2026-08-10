"""Tests for cli/draft.py."""

from unittest.mock import AsyncMock, patch

from cli import draft
from scoring.lead_scorer import score_lead


def _lead(**overrides):
    base = {
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
    }
    base.update(overrides)
    return base


class TestFindExistingSequence:
    def test_matches_by_website(self):
        lead = _lead()
        hunt_result = {
            "email_sequences": [
                {"lead": {"website": lead["website"], "company_name": "different"}, "emails": [{"subject": "s", "body": "b"}]}
            ]
        }
        sequence = draft.find_existing_sequence(hunt_result, lead)
        assert sequence is not None

    def test_returns_none_when_no_match(self):
        lead = _lead()
        hunt_result = {"email_sequences": [{"lead": {"website": "https://other.example.com"}, "emails": []}]}
        assert draft.find_existing_sequence(hunt_result, lead) is None


class TestGenerateDraft:
    def test_uses_existing_sequence_without_calling_llm(self):
        lead = _lead()
        scored = score_lead(lead)
        hunt_result = {
            "email_sequences": [
                {
                    "lead": {"website": lead["website"]},
                    "emails": [{"subject": "Existing subject", "body": "Existing body"}],
                }
            ]
        }
        with patch("cli.draft._generate_with_llm", new_callable=AsyncMock) as mock_llm:
            result = draft.generate_draft(lead, scored, hunt_result=hunt_result)

        mock_llm.assert_not_called()
        assert result["subject"] == "Existing subject"
        assert result["source"] == "existing_sequence"

    def test_falls_back_to_llm_generation(self):
        lead = _lead()
        scored = score_lead(lead)
        with patch(
            "cli.draft._generate_with_llm",
            new_callable=AsyncMock,
            return_value={"subject": "Generated subject", "body": "Generated body"},
        ):
            result = draft.generate_draft(lead, scored, hunt_result=None)

        assert result["subject"] == "Generated subject"
        assert result["source"] == "generated"
