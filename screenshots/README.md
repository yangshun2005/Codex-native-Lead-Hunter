# Screenshots / Demo GIF

`README.md` embeds `./screenshots/demo.gif`, which is intentionally not committed yet — it's a placeholder.

To record one:

1. Run the backend + frontend locally (see Quick Start in the root README).
2. Run a small hunt end to end: create a hunt, watch leads stream in, open a lead, generate an outreach draft, and (on macOS) create a Mail.app draft.
3. Record the terminal and/or browser (e.g. `asciinema`, QuickTime screen recording, or `ffmpeg`) and convert to a GIF under ~10MB, e.g.:
   ```bash
   ffmpeg -i demo.mov -vf "fps=12,scale=960:-1:flags=lanczos" -loop 0 demo.gif
   ```
4. Save it as `screenshots/demo.gif` and add a couple of static screenshots (`dashboard.png`, `lead-detail.png`, `mail-draft.png`) alongside it for the README/gallery.
