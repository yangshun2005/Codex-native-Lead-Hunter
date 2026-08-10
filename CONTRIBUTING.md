# Contributing

Thanks for considering a contribution to Codex-native Lead Hunter. This is a young rebrand of an existing pipeline, so there's plenty of room to help.

## What's especially welcome

- Bug reports with a repro (backend logs + the `lead-hunter` command that triggered it)
- Additional worked [`examples/`](./examples) for other verticals or platforms
- Platform integrations for lead discovery/verification — **as long as they respect [SAFETY.md](./SAFETY.md)**: draft-only outreach, no CAPTCHA/login bypass, no mass posting
- Improvements to the deterministic scoring model in `backend/scoring/lead_scorer.py` (or a well-justified LLM-backed alternative behind a flag)
- Additional LLM provider wiring in `backend/tools/llm_client.py` / `backend/config/settings.py`

## Development setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DEEPSEEK_API_KEY at minimum
uvicorn api.app:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

## Before opening a PR

```bash
cd backend
python -m pytest -q
ruff check .
```

- Keep changes focused — one logical change per PR.
- If you touch `backend/scoring/lead_scorer.py`, `backend/cli/`, or anything outreach-adjacent, make sure it still can't send/post anything automatically, and add/update tests under `backend/tests/test_cli/` or `backend/tests/test_scoring/`.
- Update `CHANGELOG.md` under `[Unreleased]` for user-facing changes.
- Conventional commit-style messages are appreciated (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## Suggested GitHub topics (for maintainers)

`codex`, `ai-agent`, `lead-generation`, `sales-automation`, `deepseek`, `b2b-sales`, `outreach`, `local-first`, `mail-app`, `browser-automation`

## Code of conduct

Be respectful, assume good faith, and keep discussion focused on the code. Reports of harassment or abuse can be sent to the repository owner directly.
