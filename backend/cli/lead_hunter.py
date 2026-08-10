"""lead-hunter — CLI for Codex-native Lead Hunter.

Run with: python -m cli.lead_hunter <command> [options]   (from backend/)

Talks to the local FastAPI server (start it with `uvicorn api.app:app`).
Every outreach-producing command here creates a DRAFT only — see SAFETY.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from cli import browser_verify, draft, state  # noqa: E402
from cli.api_client import ApiClient, ApiError  # noqa: E402
from cli.mail_draft import build_confirmation_summary, create_draft  # noqa: E402
from scoring.lead_scorer import lead_id as compute_lead_id  # noqa: E402
from scoring.lead_scorer import outreach_queue, score_leads  # noqa: E402


def _print(data, as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)


def _fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def _resolve_hunt_id(client: ApiClient, explicit: str | None) -> str:
    if explicit:
        return explicit
    current = state.get_current_hunt()
    if current:
        return current
    hunts = client.list_hunts()
    if not hunts:
        _fail("No hunt found. Run `lead-hunter run` first, or pass --hunt-id.")
    return hunts[0]["hunt_id"]


def _scored_leads_for_hunt(client: ApiClient, hunt_id: str) -> tuple[dict, list[dict]]:
    result = client.get_hunt_result(hunt_id)
    scored = score_leads(result.get("leads", []))
    verifications = state.all_verifications()
    for lead in scored:
        v = verifications.get(lead["id"])
        if v:
            lead["verification"] = v
    return result, scored


def _find_lead(scored_leads: list[dict], lead_id: str) -> dict:
    for lead in scored_leads:
        if lead["id"] == lead_id:
            return lead
    _fail(f"Lead '{lead_id}' not found in this hunt. Run `lead-hunter leads list` to see ids.")


def _find_raw_lead(hunt_result: dict, lead_id: str) -> dict | None:
    return next(
        (lead for lead in hunt_result.get("leads", []) if compute_lead_id(lead) == lead_id), None
    )


# ── Commands ─────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> None:
    from config.settings import get_settings
    from tools.llm_client import missing_api_key_error

    settings = get_settings()
    print("Codex-native Lead Hunter — setup check")
    print(f"  LLM_MODEL:       {settings.llm_model}")
    print(f"  REASONING_MODEL: {settings.reasoning_model}")

    models = (("LLM_MODEL", settings.llm_model), ("REASONING_MODEL", settings.reasoning_model))
    for label, model in models:
        error = missing_api_key_error(model)
        if error:
            print(f"  [!] {label}: {error}")
        else:
            print(f"  [ok] {label} has an API key configured.")

    client = ApiClient()
    try:
        client.health()
        print(f"  [ok] API server reachable at {client.base_url}")
    except ApiError as exc:
        print(f"  [!] {exc}")

    print("\nNext: python -m cli.lead_hunter run --product \"...\" --market \"...\"")


def cmd_run(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    payload = {
        "description": args.product or "",
        "product_keywords": args.keywords or [],
        "target_customer_profile": args.market or "",
        "target_regions": [args.region] if args.region else [],
        "target_lead_count": args.target_lead_count,
        "max_rounds": args.max_rounds,
        "enable_email_craft": args.enable_email_craft,
    }
    try:
        response = client.create_hunt(payload)
    except ApiError as exc:
        _fail(str(exc))

    hunt_id = response["hunt_id"]
    state.set_current_hunt(hunt_id)
    print(f"Started hunt {hunt_id}")

    if args.no_wait:
        return

    print("Waiting for results (Ctrl+C to stop watching — the hunt keeps running server-side)...")
    last_stage = None
    try:
        while True:
            status = client.get_hunt_status(hunt_id)
            rnd, leads_n = status["hunt_round"], status["leads_count"]
            stage = f"{status['status']} / round {rnd} / {leads_n} leads"
            if stage != last_stage:
                print(f"  {stage}")
                last_stage = stage
            if status["status"] in ("completed", "failed"):
                break
            time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        print("\nStopped watching. The hunt keeps running server-side. Resume with:")
        print(f"  python -m cli.lead_hunter leads list --hunt-id {hunt_id}")
        return

    if status["status"] == "failed":
        _fail(f"Hunt failed: {status.get('error', 'unknown error')}")

    _, scored = _scored_leads_for_hunt(client, hunt_id)
    queue = outreach_queue(scored)
    print(f"\nDone. {len(scored)} leads found, {len(queue)} scored fit_score >= 7 (outreach queue).")  # noqa: E501
    print(f"Next: python -m cli.lead_hunter leads list --hunt-id {hunt_id}")


def cmd_leads_list(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    hunt_id = _resolve_hunt_id(client, args.hunt_id)
    _, scored = _scored_leads_for_hunt(client, hunt_id)

    if args.min_fit_score is not None:
        scored = [lead for lead in scored if lead["fit_score"] >= args.min_fit_score]

    if args.json:
        _print({"hunt_id": hunt_id, "leads": scored}, True)
        return

    print(f"Hunt {hunt_id} — {len(scored)} lead(s)")
    for lead in scored:
        flag = "★" if lead["fit_score"] >= 7 else " "
        print(
            f"  {flag} [{lead['id']}] {lead['company']:<30.30} "
            f"fit={lead['fit_score']} conf={lead['confidence']} "
            f"action={lead['recommended_action']} email={lead['email'] or '-'}"
        )


def cmd_lead_inspect(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    hunt_id = _resolve_hunt_id(client, args.hunt_id)
    _, scored = _scored_leads_for_hunt(client, hunt_id)
    lead = _find_lead(scored, args.lead_id)
    _print(lead, True)


def cmd_draft_email(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    hunt_id = _resolve_hunt_id(client, args.hunt_id)
    result, scored = _scored_leads_for_hunt(client, hunt_id)
    scored_lead = _find_lead(scored, args.lead_id)
    raw_lead = _find_raw_lead(result, args.lead_id)
    if raw_lead is None:
        _fail("Could not locate raw lead data for this id.")

    try:
        generated = draft.generate_draft(
            raw_lead, scored_lead, hunt_result=result, product=args.product or ""
        )
    except Exception as exc:  # LLM/config errors — surface clearly, don't crash with a traceback
        _fail(f"Could not generate a draft: {exc}")

    output = {
        "lead_id": args.lead_id,
        "to": scored_lead["email"] or "(no email found — see 'risk' on this lead)",
        "subject": generated["subject"],
        "body": generated["body"],
        "source": generated["source"],
        "note": "This is a DRAFT. Nothing was sent. Review before using with mail-draft.",
    }
    _print(output, True)


def cmd_mail_draft(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    hunt_id = _resolve_hunt_id(client, args.hunt_id)
    result, scored = _scored_leads_for_hunt(client, hunt_id)
    scored_lead = _find_lead(scored, args.lead_id)

    subject, body = args.subject, args.body
    if not subject or not body:
        raw_lead = _find_raw_lead(result, args.lead_id)
        try:
            generated = draft.generate_draft(
            raw_lead, scored_lead, hunt_result=result, product=args.product or ""
        )
        except Exception as exc:
            _fail(f"Could not generate a draft: {exc}")
        subject = subject or generated["subject"]
        body = body or generated["body"]

    summary = build_confirmation_summary(
        recipient=scored_lead["email"],
        subject=subject,
        body=body,
        lead_id=args.lead_id,
        source_url=scored_lead["source_url"],
    )
    print("About to create a Mail.app DRAFT (not sent):")
    _print(summary, True)

    outcome = create_draft(
        recipient=scored_lead["email"],
        subject=subject,
        body=body,
        lead_id=args.lead_id,
        source_url=scored_lead["source_url"],
    )
    _print({"status": outcome.status, "reason": outcome.reason}, True)
    if outcome.status != "created":
        sys.exit(2)


def cmd_open(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    hunt_id = _resolve_hunt_id(client, args.hunt_id)
    _, scored = _scored_leads_for_hunt(client, hunt_id)
    lead = _find_lead(scored, args.lead_id)
    opened = browser_verify.open_lead(lead)
    if not opened:
        print("No URLs found for this lead to open.")
        return
    print(f"Opened {len(opened)} URL(s) for verification:")
    for url in opened:
        print(f"  {url}")


def cmd_verify(args: argparse.Namespace) -> None:
    entry = browser_verify.record_verification(args.lead_id, args.status, args.note or "")
    _print({"lead_id": args.lead_id, **entry}, True)


def cmd_export(args: argparse.Namespace) -> None:
    client = ApiClient(base_url=args.api_base)
    hunt_id = _resolve_hunt_id(client, args.hunt_id)
    _, scored = _scored_leads_for_hunt(client, hunt_id)

    out_path = Path(args.out) if args.out else Path(f"leads_{hunt_id[:8]}.csv")
    fieldnames = [
        "id", "company", "person", "role", "email", "website", "source_url",
        "detected_need", "business_value", "urgency", "fit_score", "confidence",
        "recommended_action", "risk", "evidence",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in scored:
            row = {k: lead.get(k, "") for k in fieldnames}
            row["evidence"] = "; ".join(lead.get("evidence") or [])
            writer.writerow(row)

    print(f"Exported {len(scored)} leads to {out_path}")


# ── Argument parsing ─────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lead-hunter", description="Codex-native Lead Hunter CLI")
    parser.add_argument("--api-base", default=None, help="Override API base URL (default: http://127.0.0.1:8000)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Check DeepSeek/API key and server setup")
    p_init.set_defaults(func=cmd_init)

    p_run = sub.add_parser("run", help="Start a new lead-hunting run")
    p_run.add_argument("--product", required=True, help="What you're selling / your product")
    p_run.add_argument("--market", default="", help="Target customer, e.g. 'dentists in CA'")
    p_run.add_argument("--region", default="", help="Target region, e.g. 'US'")
    p_run.add_argument("--keywords", nargs="*", default=[], help="Optional product keywords")
    p_run.add_argument("--target-lead-count", type=int, default=50)
    p_run.add_argument("--max-rounds", type=int, default=5)
    p_run.add_argument(
        "--enable-email-craft", action="store_true", help="Also generate AI email sequences"
    )
    p_run.add_argument("--no-wait", action="store_true", help="Return immediately, don't poll")
    p_run.add_argument("--poll-interval", type=int, default=10)
    p_run.set_defaults(func=cmd_run)

    p_leads = sub.add_parser("leads", help="Lead operations")
    leads_sub = p_leads.add_subparsers(dest="leads_command", required=True)
    p_leads_list = leads_sub.add_parser("list", help="List scored leads for a hunt")
    p_leads_list.add_argument("--hunt-id", default=None)
    p_leads_list.add_argument("--min-fit-score", type=int, default=None)
    p_leads_list.add_argument("--json", action="store_true")
    p_leads_list.set_defaults(func=cmd_leads_list)

    p_lead = sub.add_parser("lead", help="Single-lead operations")
    lead_sub = p_lead.add_subparsers(dest="lead_command", required=True)
    p_lead_inspect = lead_sub.add_parser("inspect", help="Show full scored detail for one lead")
    p_lead_inspect.add_argument("lead_id")
    p_lead_inspect.add_argument("--hunt-id", default=None)
    p_lead_inspect.set_defaults(func=cmd_lead_inspect)

    p_draft = sub.add_parser("draft-email", help="Generate an outreach email draft (text only)")
    p_draft.add_argument("lead_id")
    p_draft.add_argument("--hunt-id", default=None)
    p_draft.add_argument("--product", default="", help="Extra product/offer context for generation")
    p_draft.set_defaults(func=cmd_draft_email)

    p_mail = sub.add_parser("mail-draft", help="Create a macOS Mail.app draft for a lead")
    p_mail.add_argument("lead_id")
    p_mail.add_argument("--hunt-id", default=None)
    p_mail.add_argument("--product", default="")
    p_mail.add_argument("--subject", default=None)
    p_mail.add_argument("--body", default=None)
    p_mail.set_defaults(func=cmd_mail_draft)

    p_open = sub.add_parser("open", help="Open a lead's source/company/social URLs to verify it")
    p_open.add_argument("lead_id")
    p_open.add_argument("--hunt-id", default=None)
    p_open.set_defaults(func=cmd_open)

    p_verify = sub.add_parser("verify", help="Record a verified/rejected note for a lead")
    p_verify.add_argument("lead_id")
    p_verify.add_argument("--status", required=True, choices=["verified", "rejected"])
    p_verify.add_argument("--note", default="")
    p_verify.set_defaults(func=cmd_verify)

    p_export = sub.add_parser("export", help="Export scored leads to CSV")
    p_export.add_argument("--hunt-id", default=None)
    p_export.add_argument("--format", default="csv", choices=["csv"])
    p_export.add_argument("--out", default=None)
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ApiError as exc:
        _fail(str(exc))


if __name__ == "__main__":
    main()
