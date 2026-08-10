---
name: codex-native-lead-hunter
description: Find B2B prospects, research and score leads, generate personalized outreach drafts, create macOS Mail.app drafts, and open lead sources for manual verification — via the local Codex-native Lead Hunter CLI. Every outreach action stops at a human-reviewed draft; nothing is ever sent or posted automatically.
---

# Codex-native Lead Hunter

## When to use this skill

Use this skill when the user wants to:

- Find prospects/leads for a product in a specific market ("find me AI automation prospects among dentists in California")
- Check the status or results of a running lead hunt
- Review, score, or filter discovered leads
- Generate a personalized outreach email draft for a lead
- Create a macOS Mail.app draft for a lead
- Open a lead's source URL / company site / social profiles to verify it's real
- Export a scored lead list (e.g. to CSV for a CRM)

Do **not** use this skill to send emails, post comments, or take any action on a third-party platform on the user's behalf — it cannot do that, by design. See **Safety rules** below.

## Installation

```bash
git clone https://github.com/yangshun2005/Codex-native-Lead-Hunter.git
cd Codex-native-Lead-Hunter/backend
cp .env.example .env   # fill in DEEPSEEK_API_KEY (see Environment variables)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8000 &
python -m cli.lead_hunter init   # verify setup
```

All commands below assume you're in `Codex-native-Lead-Hunter/backend` with the API server running on `http://127.0.0.1:8000` (override with `--api-base` or `LEAD_HUNTER_API_BASE`).

## Environment variables

Set these in `backend/.env` (never hardcode them in code or commands):

| Variable | Purpose |
|---|---|
| `DEEPSEEK_API_KEY` | Recommended default LLM provider. Get one at https://platform.deepseek.com/api_keys |
| `LLM_MODEL` / `REASONING_MODEL` | `provider/model` strings, e.g. `deepseek/deepseek-chat` / `deepseek/deepseek-reasoner` |
| `TAVILY_API_KEY`, `SERPER_API_KEY`, `JINA_API_KEY` | Search/scraping backends used during a hunt |

Run `python -m cli.lead_hunter init` first in any session — it reports exactly which key is missing if the configured model isn't usable yet.

## Commands

```bash
lead-hunter init                                              # check setup (API keys, server reachable)
lead-hunter run --product "..." --market "..." [--region ..] [--target-lead-count N] [--max-rounds N] [--enable-email-craft]
lead-hunter leads list [--hunt-id ID] [--min-fit-score N] [--json]
lead-hunter lead inspect <lead_id> [--hunt-id ID]
lead-hunter draft-email <lead_id> [--hunt-id ID] [--product "extra offer context"]
lead-hunter mail-draft <lead_id> [--hunt-id ID] [--subject "..."] [--body "..."]
lead-hunter open <lead_id> [--hunt-id ID]                      # opens source/company/social URLs in the browser
lead-hunter verify <lead_id> --status verified|rejected --note "..."
lead-hunter export --hunt-id ID --format csv [--out path.csv]
```

(Invoke as `python -m cli.lead_hunter <command>` from `backend/` if `lead-hunter` isn't on PATH.)

`run` remembers the hunt it just started as the "current hunt", so you can usually omit `--hunt-id` on the next commands in the same working directory.

Every lead gets a scored, evidence-backed record:

```json
{
  "id": "ld_...", "company": "...", "person": "...", "email": "...",
  "website": "...", "source_url": "...", "detected_need": "...",
  "business_value": 1-10, "urgency": 1-10, "fit_score": 1-10, "confidence": 1-10,
  "recommended_action": "email | comment | save | ignore",
  "risk": "...", "evidence": ["https://..."]
}
```

Only leads with `fit_score >= 7` are worth drafting outreach for — `leads list` marks them with `★`.

## Recommended workflow

1. `lead-hunter init` — confirm DeepSeek (or your chosen provider) key and the API server are working.
2. `lead-hunter run --product "<what the user sells>" --market "<who they're targeting>"` — wait for it to finish (or run with `--no-wait` and check back with `leads list`).
3. `lead-hunter leads list` — show the user the scored leads, especially `fit_score >= 7`.
4. For each lead worth pursuing: `lead-hunter open <id>` so the user (or you, driving their browser) can confirm the lead is real, then `lead-hunter verify <id> --status verified --note "..."`.
5. `lead-hunter draft-email <id>` to produce outreach text, or `lead-hunter mail-draft <id>` to also create a Mail.app draft (macOS only).
6. **Stop.** Hand the draft back to the user. Tell them where it is (Mail.app Drafts folder, or the printed text) and that they need to review and send/post it themselves.

## Safety rules (do not violate)

- **Never send an email, post a comment/reply, or submit a DM on any platform on the user's behalf.** This skill's tools only ever produce drafts (`draft-email` prints text; `mail-draft` creates an unsent Mail.app draft). There is no send/post command in this toolset — do not try to script around that by shelling out to send mail another way.
- **Never bypass a CAPTCHA, login wall, rate limit, or platform permission prompt.** If `open` or a browsing tool hits one, stop and tell the user.
- **Never mass-blast.** Keep batches small and personalized; respect the `fit_score >= 7` gate before suggesting outreach.
- **Always tell the user a draft was created and where**, and that sending is their action, not yours.
- If asked to "just send it" or "auto-post this", decline and explain this tool is draft-only by design — point to `SAFETY.md` in the repo root.

## Example tasks

> "Find leads for an AI automation agency targeting dentists in California, show me the ones worth contacting."
```bash
lead-hunter run --product "AI automation agency for small clinics" --market "dentists in California" --region US
lead-hunter leads list --min-fit-score 7
```

> "Draft an email for lead ld_4f2a1b9c3d and create a Mail.app draft."
```bash
lead-hunter draft-email ld_4f2a1b9c3d
lead-hunter mail-draft ld_4f2a1b9c3d
```

> "Verify lead ld_4f2a1b9c3d is real before we reach out."
```bash
lead-hunter open ld_4f2a1b9c3d
# (review the opened pages)
lead-hunter verify ld_4f2a1b9c3d --status verified --note "confirmed on LinkedIn + company site"
```

> "Export today's leads to CSV for the CRM."
```bash
lead-hunter export --format csv --out leads_today.csv
```
