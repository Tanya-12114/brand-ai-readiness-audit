# Structured Data — Required Properties by Common @type

| @type | Required for a "complete" block | Common gap |
|---|---|---|
| `Organization` | `name`, `url`, `logo`, `sameAs` (links to official social/Wikidata profiles) | `sameAs` omitted — this is exactly the disambiguation signal covered by `freshness-corroboration` |
| `Product` | `name`, `image`, `description`, `offers.price`, `offers.priceCurrency`, `offers.availability` | price/availability only rendered client-side, not mirrored in JSON-LD |
| `Article` / `BlogPosting` | `headline`, `datePublished`, `dateModified`, `author` | no `dateModified` — makes staleness impossible for an assistant to judge |
| `LocalBusiness` | `name`, `address`, `telephone`, `openingHours` | address present in text but not in markup, or inconsistent across pages |
| `FAQPage` | `mainEntity[].name` + `.acceptedAnswer.text` | only add where the page already contains genuine Q&A content — don't fabricate |
| `HowTo` | `step[]` with `text` per step | only where content is genuinely a procedure |

## Fact-locked-in-non-text checklist
For each key fact on the page, ask: "If I strip all images, video, canvas, and client-side-only rendering, is this fact still present as text?" Common offenders:
- Pricing/spec tables rendered as an image instead of HTML `<table>`.
- Store hours or address embedded in a map widget image with no text equivalent.
- Key differentiators stated only in an infographic.
- Testimonials/reviews embedded as screenshots.

## Meta tag boilerplate check
Fetch 3+ pages and compare `<title>`/`meta[description]`. If they're identical (a common CMS default), that's the finding — not the mere presence of the tags.
