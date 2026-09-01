#!/usr/bin/env python3
"""
compose_report.py -- reference implementation of audit-orchestrator steps 4-7:
normalize IDs, deduplicate overlapping findings across sub-skills, compute
summary counts, and emit the final report matching the fixed schema.

This does NOT run the sub-skills itself (they may need different tools/live
web access per skill) -- it composes their already-produced JSON finding
arrays. A calling agent invokes each sub-skill, collects their JSON output,
and feeds all of it to this script (or reimplements the same logic).

Usage:
  python compose_report.py <site> <sub_skill_output_1.json> [<sub_skill_output_2.json> ...]

Each input file must be a JSON array of findings in the shared shape:
  {"id": "...", "title": "...", "severity": "...", "evidence": "...",
   "suggested_action": {"summary": "...", "priority": "..."}}

Prints the final composed report JSON to stdout.
"""
import sys
import json
import datetime
import re

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


STOPWORDS = {
    "the", "a", "an", "on", "in", "of", "no", "not", "and", "or", "to", "for",
    "is", "was", "were", "be", "been", "with", "found", "page", "pages",
    "found.", "at", "this", "that", "any", "none", "signal", "content", "data",
}


def normalize_words(text):
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return words - STOPWORDS


def similar(a, b, threshold=0.75, min_shared=3):
    """
    Keyword-overlap similarity between two findings' title+evidence, after
    stripping common/stopword noise. Requires BOTH a high overlap ratio AND a
    minimum number of shared distinctive terms, so that two findings which
    merely mention a related concept in passing (e.g. one about missing
    JSON-LD entirely, another about a missing date *within* JSON-LD) are not
    incorrectly collapsed into one. When in doubt, findings are kept separate
    -- an orchestrator that over-merges hides real distinct problems from the
    reader, which is worse than a report with two adjacent similar items.
    """
    wa = normalize_words(a["title"] + " " + a["evidence"])
    wb = normalize_words(b["title"] + " " + b["evidence"])
    if not wa or not wb:
        return False
    shared = wa & wb
    overlap = len(shared) / min(len(wa), len(wb))
    return overlap >= threshold and len(shared) >= min_shared


def merge_pair(a, b):
    """Merge two findings judged to be duplicates: higher severity wins, evidence concatenated."""
    sev = a if SEVERITY_ORDER[a["severity"]] <= SEVERITY_ORDER[b["severity"]] else b
    other = b if sev is a else a
    merged = dict(sev)
    if other["evidence"] not in merged["evidence"]:
        merged["evidence"] = merged["evidence"] + " | Also observed: " + other["evidence"]
    # keep whichever suggested_action is longer/more specific
    if len(other.get("suggested_action", {}).get("summary", "")) > len(merged.get("suggested_action", {}).get("summary", "")):
        merged["suggested_action"] = other["suggested_action"]
    merged["source_check"] = ", ".join(filter(None, [a.get("source_check"), b.get("source_check")]))
    return merged


def dedupe(findings):
    result = []
    used = [False] * len(findings)
    for i, f in enumerate(findings):
        if used[i]:
            continue
        merged = f
        for j in range(i + 1, len(findings)):
            if used[j]:
                continue
            if similar(merged, findings[j]):
                merged = merge_pair(merged, findings[j])
                used[j] = True
        used[i] = True
        result.append(merged)
    return result


def compose(site, all_findings):
    # tag source_check if not already present, then dedupe
    deduped = dedupe(all_findings)
    deduped.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 4))

    final_findings = []
    for i, f in enumerate(deduped, start=1):
        nf = dict(f)
        nf["id"] = f"F-{i:03d}"
        final_findings.append(nf)

    counts = {}
    for f in final_findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    summary = {"total_findings": len(final_findings)}
    for sev in ("critical", "high", "medium", "low"):
        if counts.get(sev):
            summary[sev] = counts[sev]

    return {
        "site": site,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "findings": final_findings,
    }


def load_findings_file(path):
    """
    Read a sub-skill's JSON output robustly. Windows shells (PowerShell's `>`
    redirect in particular) often save redirected stdout as UTF-16 with a BOM
    rather than UTF-8, which silently corrupts a naive utf-8 read instead of
    raising a clear error. Try utf-8-sig first (handles a UTF-8 BOM cleanly),
    then fall back to utf-16, then plain utf-8, before giving up.
    """
    last_err = None
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=encoding) as fh:
                return json.load(fh)
        except (UnicodeError, json.JSONDecodeError) as e:
            last_err = e
            continue
    raise ValueError(f"Could not parse {path} as JSON with any known encoding: {last_err}")


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: compose_report.py <site> <sub_skill_output.json> [...]")
    site = sys.argv[1]
    all_findings = []
    for path in sys.argv[2:]:
        data = load_findings_file(path)
        if isinstance(data, list):
            all_findings.extend(data)

    report = compose(site, all_findings)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
