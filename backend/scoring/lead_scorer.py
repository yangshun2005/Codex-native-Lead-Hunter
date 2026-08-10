"""Deterministic lead-scoring enrichment layer.

This sits *on top of* the existing LangGraph pipeline output (`LeadInfo` /
`match_score`) rather than inside it, so it never touches the tested
extraction/evaluation agents. It's what the `lead-hunter` CLI uses to decide
what belongs in the outreach queue.

No LLM calls — purely a function of the fields the pipeline already
extracted, so it's free and instant to run over an entire hunt result.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

_URGENCY_HINTS = re.compile(
    r"\b(urgent|hiring|now hiring|looking for|need|needed|rfp|request for proposal|immediately)\b",
    re.IGNORECASE,
)
_GENERIC_EMAIL_PREFIXES = ("info@", "sales@", "contact@", "support@", "hello@", "admin@")


def lead_id(lead: dict[str, Any]) -> str:
    """Stable id derived from company + website, independent of list ordering."""
    basis = f"{lead.get('company_name', '')}|{lead.get('website', '')}".lower().strip()
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:10]
    return f"ld_{digest}"


def _clamp(value: float, low: int = 1, high: int = 10) -> int:
    return max(low, min(high, round(value)))


def _evidence(lead: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    website = str(lead.get("website") or "").strip()
    if website:
        evidence.append(website)
    for url in (lead.get("social_media") or {}).values():
        if url and url not in evidence:
            evidence.append(url)
    return evidence


def _confidence(lead: dict[str, Any]) -> int:
    signals = 0
    if lead.get("emails"):
        signals += 1
    if lead.get("phone_numbers"):
        signals += 1
    if lead.get("contact_person"):
        signals += 1
    if lead.get("social_media"):
        signals += 1
    if lead.get("website"):
        signals += 1
    # 0-5 signals -> 2-10 confidence, roughly linear.
    return _clamp(2 + signals * 1.6)


def _business_value(lead: dict[str, Any], match_score: float) -> int:
    value = match_score * 10
    if lead.get("emails"):
        value += 1
    if lead.get("contact_person"):
        value += 1
    return _clamp(value)


def _urgency(lead: dict[str, Any]) -> int:
    haystack = " ".join(
        str(lead.get(field, "")) for field in ("source_keyword", "industry")
    )
    return 7 if _URGENCY_HINTS.search(haystack) else 5


def _risk(lead: dict[str, Any]) -> str:
    emails = lead.get("emails") or []
    if not emails:
        return "no direct email found — verify contact before outreach"
    if all(any(e.lower().startswith(p) for p in _GENERIC_EMAIL_PREFIXES) for e in emails):
        return "only generic inbox (info@/sales@) found — lower reply odds, verify a named contact"
    return ""


def _recommended_action(fit_score: int, lead: dict[str, Any]) -> str:
    has_email = bool(lead.get("emails"))
    has_social = bool(lead.get("social_media"))
    if fit_score < 5:
        return "ignore"
    if fit_score < 7:
        return "save"
    if has_email:
        return "email"
    if has_social:
        return "comment"
    return "save"


def score_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """Return the extended scoring dict for a single `LeadInfo`-shaped dict.

    `match_score` (0.0-1.0, produced by the LeadExtractAgent) is the seed
    signal; everything else here is a deterministic heuristic layered on top.
    """
    match_score = float(lead.get("match_score") or 0.0)
    fit_score = _clamp(match_score * 10)
    emails = lead.get("emails") or []
    source_keyword = str(lead.get("source_keyword") or "").strip()

    return {
        "id": lead_id(lead),
        "company": lead.get("company_name", ""),
        "person": lead.get("contact_person") or "",
        "role": "",
        "email": emails[0] if emails else "",
        "website": lead.get("website", ""),
        "source_url": lead.get("website", ""),
        "detected_need": f"matched search keyword: {source_keyword}" if source_keyword else "",
        "business_value": _business_value(lead, match_score),
        "urgency": _urgency(lead),
        "fit_score": fit_score,
        "confidence": _confidence(lead),
        "recommended_action": _recommended_action(fit_score, lead),
        "risk": _risk(lead),
        "evidence": _evidence(lead),
    }


def score_leads(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [score_lead(lead) for lead in leads]


def outreach_queue(
    scored_leads: list[dict[str, Any]], min_fit_score: int = 7
) -> list[dict[str, Any]]:
    """Leads eligible for outreach draft generation — fit_score >= threshold only."""
    return [lead for lead in scored_leads if lead["fit_score"] >= min_fit_score]
