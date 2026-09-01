# Web Dashboard (optional add-on)

A tiny local Flask app that gives you a URL input box and a formatted report
instead of running the four scripts by hand and reading raw JSON.

**This is a convenience/demo tool only — it is not part of the hackathon
submission.** The submission is the `marketplace.json` + `skills/` structure
described in the root `README.md`. This dashboard just calls the same
scripts under the hood.

## Setup

From inside this `web-dashboard/` folder:

```powershell
pip install flask requests beautifulsoup4
python app.py
```

Then open **http://127.0.0.1:5000** in your browser, enter a URL, and click
"Run audit". It runs the same four sub-skill scripts as the command-line
workflow, composes them the same way `compose_report.py` does, and renders
the result as a readable report with color-coded severities instead of raw
JSON.

## Notes

- Each audit can take 10-30+ seconds depending on the target site (same as
  running the scripts manually — this isn't doing anything faster, just
  presenting it more readably).
- If a target site blocks automated requests or rate-limits, you'll see that
  reflected in the findings (e.g. "Linked pages return errors") — see the
  root README's note about telling genuine broken links apart from
  bot-blocking/rate-limiting.
- Like the scripts it wraps, this only covers static-HTML checks. It does
  not execute JavaScript or run live web searches, so findings from
  `engagement-audit`'s runtime checks and `freshness-corroboration`'s
  cross-web corroboration checks will show as "not verified in static mode"
  — same as the command-line flow.
