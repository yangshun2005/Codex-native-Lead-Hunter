# Example: Reddit opportunity finder

**Scenario:** Surface people publicly complaining about manual/tedious outreach work, as a signal they might want a tool like this one — **not** to auto-comment or mass-reply to them.

## Run it

```bash
cd backend
python -m cli.lead_hunter run \
  --product "Codex-native lead generation + outreach drafting tool" \
  --market "people complaining about manual, repetitive outreach/prospecting work" \
  --target-lead-count 15

python -m cli.lead_hunter leads list --min-fit-score 7
python -m cli.lead_hunter open <lead_id>     # opens the actual Reddit thread to read context first
python -m cli.lead_hunter draft-email <lead_id> --product "context: this is a comment reply, not an email"
```

## Sample output

[`sample-leads.json`](./sample-leads.json) and [`sample-comment-draft.json`](./sample-comment-draft.json) show the shape of what this produces: a thread URL as `evidence`, and a short, non-salesy comment draft referencing the actual complaint.

## Important: this generates drafts only

**Nothing in this repository posts a comment, reply, or DM to Reddit automatically.** `draft-email`'s output here is meant to be read by a human and, if they choose to, manually pasted as a Reddit comment — ideally *without* an overt pitch, since unsolicited self-promotion violates most subreddits' rules and Reddit's own [self-promotion guidance](https://support.reddithelp.com). If you want to actually engage, disclose who you are, add value first, and follow each subreddit's rules. See [SAFETY.md](../../SAFETY.md).
