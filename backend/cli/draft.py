"""Outreach draft generation — used by `draft-email` and `mail-draft`.

Prefers an existing AI-generated email sequence from the hunt result (created
when the hunt ran with --enable-email-craft). Falls back to a single
on-demand LLM call (via the configured provider — DeepSeek by default) when
no sequence exists yet. Either way this only ever produces a draft string;
nothing here sends anything.
"""

from __future__ import annotations

import asyncio
from typing import Any

_PROMPT_TEMPLATE = """You are drafting a short, personalized first-touch outreach email.

Sender's product/offer: {product}

Prospect:
- Company: {company}
- Industry: {industry}
- Contact: {person}
- Why they matched: {detected_need}

Write a concise (under 120 words), specific, non-spammy email. No generic
flattery, no "I hope this email finds you well". Reference something
concrete about the prospect. End with a low-friction call to action (a
question, not a meeting demand).

Respond with strict JSON: {{"subject": "...", "body": "..."}}"""


def find_existing_sequence(
    hunt_result: dict[str, Any], lead: dict[str, Any]
) -> dict[str, Any] | None:
    """Find an already-generated EmailSequence for this lead, if email craft ran during the hunt."""
    website = str(lead.get("website") or "").strip().lower()
    company = str(lead.get("company_name") or "").strip().lower()
    for sequence in hunt_result.get("email_sequences") or []:
        seq_lead = sequence.get("lead") or {}
        if str(seq_lead.get("website", "")).strip().lower() == website and website:
            return sequence
        if str(seq_lead.get("company_name", "")).strip().lower() == company and company:
            return sequence
    return None


async def _generate_with_llm(
    lead: dict[str, Any], scored: dict[str, Any], product: str
) -> dict[str, str]:
    from tools.llm_client import LLMTool
    from tools.llm_output import parse_json

    fallback_product = "(no product description — keep it generic but specific to the company)"
    prompt = _PROMPT_TEMPLATE.format(
        product=product or fallback_product,
        company=lead.get("company_name", ""),
        industry=lead.get("industry", ""),
        person=lead.get("contact_person") or "the team",
        detected_need=scored.get("detected_need") or "general fit based on search match",
    )
    tool = LLMTool(model_type="default")
    raw = await tool.generate(prompt, response_format={"type": "json_object"})
    data = parse_json(raw, context="cli.draft_email")
    if not isinstance(data, dict):
        return {"subject": "", "body": raw}
    return {"subject": str(data.get("subject", "")), "body": str(data.get("body", ""))}


def generate_draft(
    lead: dict[str, Any],
    scored: dict[str, Any],
    hunt_result: dict[str, Any] | None = None,
    product: str = "",
) -> dict[str, Any]:
    """Return {"subject", "body", "source"} — source is 'existing_sequence' or 'generated'."""
    if hunt_result:
        sequence = find_existing_sequence(hunt_result, lead)
        if sequence and sequence.get("emails"):
            first_email = sequence["emails"][0]
            return {
                "subject": first_email.get("subject", ""),
                "body": first_email.get("body", ""),
                "source": "existing_sequence",
            }

    generated = asyncio.run(_generate_with_llm(lead, scored, product))
    return {**generated, "source": "generated"}
