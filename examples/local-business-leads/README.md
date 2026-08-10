# Example: Local business leads

**Scenario:** An AI automation agency wants to find dental clinics in California that might want automated scheduling/reminders.

## Run it

```bash
cd backend
python -m cli.lead_hunter run \
  --product "AI automation agency — automated scheduling, reminders, and intake for local clinics" \
  --market "dentists in California" \
  --region US \
  --target-lead-count 30

python -m cli.lead_hunter leads list --min-fit-score 7
python -m cli.lead_hunter draft-email <lead_id>
python -m cli.lead_hunter mail-draft <lead_id>   # macOS only, creates a draft — does not send
```

## Sample output

[`sample-leads.json`](./sample-leads.json) shows the shape of scored leads this produces (illustrative sample data, not a live hunt result). [`sample-email-draft.json`](./sample-email-draft.json) shows what `draft-email` returns for the top lead.

Only the `fit_score >= 7` lead is worth drafting for — the second sample lead shows what a low-fit result looks like and why it's routed to `save` instead of `email`.
