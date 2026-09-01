---
name: engagement-audit
description: Check on-site engagement mechanics — whether a visitor who lands on the page can tell where they are and what to do next, whether context/orientation is preserved as they move through the site, and whether common bounce-inducing patterns are present. Use when traffic/citations are healthy but visitors leave quickly without acting, or when diagnosing the "keep the visitor once they arrive" half of the brief.
license: MIT
allowed-tools: ["bash", "web_fetch"]
---

# On-Site Engagement Audit

## When to use
Use for the on-site half of the audit, independent of the discoverability skills — a page can be perfectly crawlable, structured, and corroborated and still lose visitors on arrival. This skill checks the mechanics that make a landing feel oriented and purposeful versus disorienting or dead-ended, since these are the concrete, observable proxies for what turns an arrival into an engaged visit.

## Inputs
- `url` (required): the page(s) a visitor is likely to land on first (homepage plus 1-2 likely deep-link targets, since AI-assistant traffic often lands deep rather than on the homepage).
- `html` (optional): already-fetched content to avoid re-fetching.

## Procedure
1. **Orientation check**: does the page, within the first visible screen's worth of content, make clear (a) what this is/who it's for, and (b) where the visitor is within the site (breadcrumbs, active nav state, section label)? A deep-linked page with no breadcrumb/back-to-context path and no restated context (assumes the visitor arrived via the homepage) → **high** finding — this matters more than usual because AI-assistant referrals frequently land deep, skipping the homepage's context-setting.
2. **Clear next step**: identify the single most important action the page wants a visitor to take (buy, sign up, read more, contact). Is there one unambiguous, visible call-to-action, or are there many competing/no CTAs? Zero clear CTA on a page that clearly has a commercial/conversion purpose → **medium** finding. Many competing CTAs with no visual hierarchy → **low** finding.
3. **Navigation depth & findability**: from the landing page, can a visitor reach the site's 2-3 most likely next destinations (pricing, contact, related content) within 1-2 clicks via visible links (not just a hidden hamburger menu with no labels)? If not → **medium** finding.
4. **Context retention across navigation**: check whether key state a visitor set (e.g. a selected product variant, a filter, a search query) survives a client-side navigation or is silently lost, forcing re-entry. This is a **medium** finding when reproducible (e.g. going deep-link to another page and back resets a plainly session-scoped choice with no reason to reset it).
5. **Bounce-inducing patterns**: check for and flag if present — an interstitial/modal blocking content before any value is shown (e.g. a signup wall or cookie banner covering the main content with no easy dismiss), autoplay audio/video, or content that visibly shifts/reflows after load (layout instability). Any of these on a first-touch landing page → **high** finding (measurably drives immediate exits regardless of content quality).
6. **Mobile viability**: check for a `<meta name="viewport">` tag and that primary content/nav isn't obviously fixed-width beyond typical mobile widths. Missing viewport meta on a public page → **high** finding, since a large share of AI-assistant-referred traffic is mobile.
7. **Trust/credibility signals appropriate to the page's purpose**: visible contact info or support path, and (for commercial pages) some legitimacy signal (reviews, case studies, recognizable proof points). Total absence on a page asking for money/contact info → **medium** finding.

## Output
Same finding shape, `id` prefix `EN-`. Return `[]` where nothing is wrong; don't force a finding for every check. As a proactive suggestion beyond defects, consider recommending a short "you might also want" / related-content module on deep-linked pages specifically to compensate for visitors skipping the homepage's context — flag as `low`/`medium` priority even where no explicit defect triggered it.

See `references/checklist.md` for the full pass/fail table and reasoning per check, and `scripts/engagement_check.py` for a runnable reference implementation of the checks that are inferable from static HTML (1, 2, 3, 6, 7); checks 4-5 involve client-side behavior and are best confirmed by the calling agent with a browser-rendering tool if available, or noted as "unable to verify without JS execution" otherwise.
