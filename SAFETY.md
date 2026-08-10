# Safety & Anti-Spam Policy

Codex-native Lead Hunter is a research and drafting tool, not a spam cannon. If you're evaluating whether to use it, or extending it, this document is the contract.

## 1. This is not a spam tool

The project exists to help you send *fewer, better-targeted* emails — not more, generic ones. The [lead scoring model](./skills/codex-native-lead-hunter/SKILL.md) exists specifically to keep the outreach queue small: only leads with `fit_score >= 7`, backed by cited evidence, are recommended for outreach at all.

## 2. Nothing sends or posts automatically

Every command that produces outreach content stops at a **draft**:

- `lead-hunter draft-email` prints text to your terminal. It does not send anything, anywhere.
- `lead-hunter mail-draft` creates a real draft in macOS Mail.app via AppleScript. There is no "send" step in that AppleScript — the draft sits in your Drafts folder until **you** open Mail.app and click Send.
- Comment/reply drafts shown in `examples/reddit-opportunity-finder/` are text output only. Nothing is posted to Reddit, X, LinkedIn, or any other platform by this codebase.

If you (or an agent driving this tool) want an email actually sent, that is a deliberate, separate, human action outside this tool's scope by design.

## 3. No bypassing platform protections

This project will not, and must not be extended to:

- Solve, bypass, or work around CAPTCHAs
- Bypass login walls, paywalls, or authentication
- Circumvent platform rate limits, permission scopes, or bot-detection
- Scrape data a platform's terms of service prohibit accessing programmatically

If a verification or research step in the workflow hits one of these, the correct behavior is to stop and hand it back to the human, not find a workaround.

## 4. No mass / low-quality outreach

- Default batch sizes and the `fit_score >= 7` gate exist to keep outreach small and personalized. Don't raise `target_lead_count` into the thousands and blast every result.
- Every lead carries `evidence` (a source URL) so a human can sanity-check it's a real prospect before any draft is written, not a scraped list with no paper trail.
- Outreach content should reference something specific and true about the prospect — not a templated mail-merge.

## 5. Your responsibility

You are responsible for:

- Complying with each platform's Terms of Service (Gmail/Google Workspace sending limits, LinkedIn's automation policy, Reddit's self-promotion rules, X's platform rules, etc.)
- Complying with applicable anti-spam and privacy law in your jurisdiction and your recipients' — e.g. **CAN-SPAM** (US), **PECR/UK GDPR** (UK), **GDPR** (EU), **CASL** (Canada). This typically means: identify yourself, don't use deceptive subject lines, include an unsubscribe/opt-out path, and honor opt-outs.
- Only contacting people/companies where you have a legitimate reason to believe outreach is appropriate (B2B decision-makers about a relevant product is generally lower-risk than cold consumer outreach — but local law still applies).
- Reviewing every draft before sending it. This tool does not indemnify you against sending something wrong, and human review is the whole point of the design.

## 6. Reporting a safety issue

If you find a way this tool (or a fork of it) could be used to send/post without human review, bypass a platform protection, or otherwise violate this policy, please open an issue rather than a PR that "fixes" it by removing a safeguard.
