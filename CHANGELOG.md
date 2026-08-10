# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Repositioned the project as **Codex-native Lead Hunter** — open-source, local-first, Codex/Claude Code/Cursor-driven lead generation agent.
- DeepSeek-first LLM provider configuration (`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `LLM_MODEL=deepseek/deepseek-chat`, `REASONING_MODEL=deepseek/deepseek-reasoner` as defaults), alongside the existing OpenAI/Anthropic/OpenRouter/Groq/GLM/Moonshot/MiniMax support. Clear startup warning when the configured provider's API key is missing.
- `lead-hunter` CLI (`backend/cli/`) — `init`, `run`, `leads list`, `lead inspect`, `draft-email`, `mail-draft`, `open`, `verify`, `export`.
- macOS Mail.app draft generation (`cli/mail_draft.py`) — creates a real, unsent Mail.app draft via AppleScript; never sends.
- Browser-assisted lead verification (`cli/browser_verify.py`) — opens a lead's source/company/social URLs and records verified/rejected notes locally.
- Deterministic lead-scoring enrichment layer (`backend/scoring/lead_scorer.py`) producing `fit_score`, `business_value`, `urgency`, `confidence`, `recommended_action`, `risk`, and `evidence` for every lead, on top of the existing `match_score`.
- Codex/Claude Code/Cursor [Skill](./skills/codex-native-lead-hunter/SKILL.md) documenting safe, agent-driven usage.
- [SAFETY.md](./SAFETY.md) — the human-approval / anti-spam policy this project commits to.
- `examples/` — four runnable end-to-end scenarios (local business leads, GitHub project prospecting, Reddit opportunity finding, CSV export).

### Fixed
- Added missing `dnspython` dependency to `requirements.txt` (used by `tools/email_verifier.py`'s MX-record lookup; tests for it were failing without it).

### Removed
- Old project marketing assets (WeChat/payment QR codes) not relevant to the new positioning.

## Base project

This project builds on the open-source [AI_Find_Customer](https://github.com/xiongQvQ/AI_Find_Customer) multi-agent B2B lead-hunting pipeline (LangGraph + FastAPI + React). See that project's history for everything prior to this rebrand.
