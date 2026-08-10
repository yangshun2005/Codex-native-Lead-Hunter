# Roadmap

## Done

- [x] Multi-agent lead discovery pipeline (`Insight -> KeywordGen -> Search -> LeadExtract -> Evaluate`), LangGraph-orchestrated
- [x] DeepSeek-first, provider-agnostic LLM config (LiteLLM)
- [x] `lead-hunter` CLI: `init`, `run`, `leads list`, `lead inspect`, `draft-email`, `mail-draft`, `open`, `verify`, `export`
- [x] macOS Mail.app draft generation (AppleScript, draft-only)
- [x] Deterministic lead scoring (`fit_score`, `business_value`, `urgency`, `confidence`, `recommended_action`, `risk`, `evidence`)
- [x] Codex/Claude Code/Cursor Skill
- [x] Safety model + anti-spam policy (SAFETY.md)
- [x] Runnable examples (local business, GitHub prospecting, Reddit opportunity-finding, CSV export)

## Next

- [ ] Native Chrome/Playwright/browser-use-driven verification — today `lead-hunter open` just opens URLs in your default browser; a richer version could navigate, take a screenshot, and extract confirmation evidence automatically (still stopping short of any write action).
- [ ] `console_scripts` packaging so `pip install -e backend` gives you a real `lead-hunter` binary instead of `python -m cli.lead_hunter`.
- [ ] Windows/Linux equivalent of Mail.app drafts — e.g. exporting an `.eml` file you can open in any mail client, or a Gmail-drafts-API integration that still stops at draft creation.
- [ ] LLM-backed `detected_need` / `urgency` scoring (currently heuristic/deterministic) as an optional, explicitly-costed upgrade to the scoring layer.
- [ ] First-class Reddit/X/LinkedIn "opportunity finder" commands beyond the example scripts, still draft-only.
- [ ] Packaged desktop app auto-update path for the CLI/skill alongside the existing Electron-style backend packaging.

## Explicitly out of scope

- Automatic sending of email, or automatic posting/commenting/DMing on any third-party platform. See [SAFETY.md](./SAFETY.md) — this is a permanent design constraint, not a temporary gap.
- CAPTCHA solving, login/permission bypass, or bot-detection evasion of any kind.
