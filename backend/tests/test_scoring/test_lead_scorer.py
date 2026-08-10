"""Tests for scoring/lead_scorer.py."""

from scoring.lead_scorer import lead_id, outreach_queue, score_lead, score_leads


def _lead(**overrides):
    base = {
        "company_name": "Acme Dental",
        "website": "https://acmedental.example.com",
        "industry": "Dental",
        "emails": ["owner@acmedental.example.com"],
        "phone_numbers": ["+1-555-0100"],
        "social_media": {"linkedin": "https://linkedin.com/company/acme-dental"},
        "contact_person": "Jane Doe",
        "country_code": "US",
        "source_keyword": "dentists in California",
        "match_score": 0.85,
    }
    base.update(overrides)
    return base


class TestLeadId:
    def test_stable_across_calls(self):
        lead = _lead()
        assert lead_id(lead) == lead_id(_lead())

    def test_differs_for_different_company(self):
        assert lead_id(_lead()) != lead_id(_lead(company_name="Other Co"))


class TestScoreLead:
    def test_high_match_score_produces_high_fit_score(self):
        scored = score_lead(_lead(match_score=0.9))
        assert scored["fit_score"] == 9
        assert scored["recommended_action"] == "email"

    def test_low_match_score_is_not_recommended_for_outreach(self):
        scored = score_lead(_lead(match_score=0.2, emails=[], phone_numbers=[], social_media={}, contact_person=None))
        assert scored["fit_score"] <= 4
        assert scored["recommended_action"] == "ignore"

    def test_no_email_but_social_recommends_comment(self):
        scored = score_lead(_lead(match_score=0.8, emails=[]))
        assert scored["recommended_action"] == "comment"

    def test_risk_flagged_for_generic_email_only(self):
        scored = score_lead(_lead(emails=["info@acmedental.example.com"]))
        assert "generic" in scored["risk"]

    def test_risk_empty_for_named_contact_email(self):
        scored = score_lead(_lead(emails=["jane@acmedental.example.com"]))
        assert scored["risk"] == ""

    def test_evidence_includes_website_and_social(self):
        scored = score_lead(_lead())
        assert "https://acmedental.example.com" in scored["evidence"]
        assert "https://linkedin.com/company/acme-dental" in scored["evidence"]

    def test_output_schema_keys(self):
        scored = score_lead(_lead())
        expected_keys = {
            "id", "company", "person", "role", "email", "website", "source_url",
            "detected_need", "business_value", "urgency", "fit_score", "confidence",
            "recommended_action", "risk", "evidence",
        }
        assert expected_keys.issubset(scored.keys())


class TestScoreLeads:
    def test_scores_each_lead(self):
        scored = score_leads([_lead(), _lead(company_name="Beta Co", match_score=0.3)])
        assert len(scored) == 2
        assert scored[0]["company"] == "Acme Dental"
        assert scored[1]["company"] == "Beta Co"


class TestOutreachQueue:
    def test_filters_by_min_fit_score(self):
        scored = [
            score_lead(_lead(match_score=0.9)),
            score_lead(_lead(company_name="Low Fit", match_score=0.3, emails=[], phone_numbers=[], social_media={}, contact_person=None)),
        ]
        queue = outreach_queue(scored, min_fit_score=7)
        assert len(queue) == 1
        assert queue[0]["company"] == "Acme Dental"
