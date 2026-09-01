# Audit Report — Annotated Schema

This is the fixed shape the entrypoint must emit. Fields marked **required** are the contest floor;
everything else is optional and may be extended freely.

```json
{
  "site": "example.com",                 // required: normalized domain/URL that was audited
  "audited_at": "2026-09-20T14:32:00Z",  // required: ISO-8601 UTC timestamp of when the audit ran
  "summary": {                            // required: counts-by-severity, only present severities included
    "total_findings": 6,                  // required
    "critical": 1,                        // optional key, include only if > 0
    "high": 2,                            // optional key, include only if > 0
    "medium": 3,                          // optional key, include only if > 0
    "low": 0                              // optional key, include only if > 0
  },
  "findings": [                           // required: array, may be empty if genuinely nothing found
    {
      "id": "F-001",                      // required: sequential, unique within this report
      "title": "short description",       // required: human-scannable one-liner
      "severity": "critical|high|medium|low", // required
      "evidence": "concrete, specific, falsifiable observation — numbers, URLs, snippets of what was checked, not a general claim", // required
      "suggested_action": {                // required
        "summary": "what to change and how, specific enough to act on without further research",
        "priority": "critical|high|medium|low" // required, may differ from finding severity if urgency differs from impact
      },
      "source_check": "crawl-render-audit:CR-001",  // optional but recommended: traceability back to which sub-skill/check produced this
      "category": "discoverability|engagement"       // optional but recommended: which half of the brief this addresses
    }
  ]
}
```

## Ordering
`findings` should be sorted by descending severity (`critical`, `high`, `medium`, `low`), and by discovery order within a severity tier, so a reader scans the most important items first.

## What NOT to include
- No fields that describe destructive or site-altering actions — `suggested_action.summary` is always a recommendation to a human/dev team, never an instruction the marketplace itself carried out.
- No fabricated evidence — if a check could not be completed (e.g. no JS-execution tool available), say so explicitly in `evidence` rather than guessing, and consider `severity: "low"` with a note to re-run with fuller tooling (see `engagement-audit`'s `EN-NOTE-*` pattern).
