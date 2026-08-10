# Example: GitHub project prospecting

**Scenario:** A developer-tools startup wants to find open-source maintainers whose projects would benefit from (or complement) their tool, to explore integration/partnership conversations — not to spam maintainers with generic pitches.

## Run it

```bash
cd backend
python -m cli.lead_hunter run \
  --product "Hosted CI cache layer for monorepo build tools" \
  --market "maintainers of open-source build-tool and monorepo projects looking for faster CI" \
  --target-lead-count 20

python -m cli.lead_hunter leads list --min-fit-score 7
python -m cli.lead_hunter open <lead_id>          # opens the repo/profile to confirm it's active & real
python -m cli.lead_hunter verify <lead_id> --status verified --note "active repo, maintainer responsive on issues"
python -m cli.lead_hunter draft-email <lead_id>
```

## Sample output

[`sample-leads.json`](./sample-leads.json) — note `recommended_action: "comment"` for the lead with no public email but an active GitHub profile: the scoring layer routes contact-less-but-social leads toward a lower-friction channel (a comment/issue reply) rather than inventing an email address.

[`sample-outreach-draft.json`](./sample-outreach-draft.json) shows the personalized draft for the top lead — referencing the actual project, not a generic template.

**Note:** this example produces text drafts only. It does not open a GitHub issue, PR, or discussion on your behalf — see [SAFETY.md](../../SAFETY.md).
