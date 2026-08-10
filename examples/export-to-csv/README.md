# Example: Export to CSV

**Scenario:** You've run a hunt and want the scored lead list in your CRM (or a spreadsheet) instead of the terminal.

## Run it

```bash
cd backend
python -m cli.lead_hunter export --hunt-id <hunt_id> --format csv --out leads.csv
```

If you omit `--hunt-id`, it uses the most recent hunt (the one `run` last started, or the newest one on the server).

## Sample output

[`sample-export.csv`](./sample-export.csv) shows the columns produced: `id, company, person, role, email, website, source_url, detected_need, business_value, urgency, fit_score, confidence, recommended_action, risk, evidence`. `evidence` is a `;`-joined list of source URLs so it stays a single CSV cell.

Import this directly into Google Sheets, Airtable, HubSpot, or any CRM that accepts CSV.
