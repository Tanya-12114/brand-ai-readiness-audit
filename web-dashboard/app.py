"""
app.py -- a small local web dashboard for the brand-ai-readiness-audit marketplace.

This is a convenience/demo tool, NOT part of the hackathon submission zip.
It runs the same skill scripts you'd run from the command line, just via a
form in your browser instead of typing four commands by hand.

Setup (from inside brand-ai-readiness-audit/web-dashboard/):
    pip install flask requests beautifulsoup4
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""
import subprocess
import sys
import json
import importlib.util
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

# Resolve paths relative to this file so it works regardless of cwd.
ROOT = Path(__file__).resolve().parent.parent  # brand-ai-readiness-audit/
SCRIPTS = {
    "crawl": ROOT / "skills" / "crawl-render-audit" / "scripts" / "crawl_check.py",
    "structured": ROOT / "skills" / "structured-data-audit" / "scripts" / "structured_data_check.py",
    "freshness": ROOT / "skills" / "freshness-corroboration" / "scripts" / "corroboration_check.py",
    "engagement": ROOT / "skills" / "engagement-audit" / "scripts" / "engagement_check.py",
}
COMPOSE_SCRIPT = ROOT / "skills" / "audit-orchestrator" / "scripts" / "compose_report.py"


def _load_compose_module():
    """compose_report.py lives under a hyphenated folder name, so it can't be
    imported normally -- load it directly from its file path instead."""
    spec = importlib.util.spec_from_file_location("compose_report", COMPOSE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_check(script_path, url, timeout=90):
    """Run one sub-skill script and parse its JSON stdout. Returns
    (findings_list, error_message_or_None)."""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), url],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return [], f"Timed out after {timeout}s"

    if result.returncode != 0:
        return [], (result.stderr.strip() or "Script exited with an error")

    try:
        data = json.loads(result.stdout)
        return (data if isinstance(data, list) else []), None
    except json.JSONDecodeError:
        return [], "Could not parse script output as JSON"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", report=None, site=None, errors=None)

    site_input = request.form.get("url", "").strip()
    if not site_input:
        return render_template("index.html", report=None, site=None,
                                errors=["Please enter a URL."])

    url = site_input if site_input.startswith(("http://", "https://")) else f"https://{site_input}"

    all_findings = []
    errors = []
    for label, script in SCRIPTS.items():
        findings, err = run_check(script, url)
        all_findings.extend(findings)
        if err:
            errors.append(f"{label}-check: {err}")

    compose = _load_compose_module()
    display_site = url.split("//", 1)[-1]
    report = compose.compose(display_site, all_findings)

    return render_template("index.html", report=report, site=display_site,
                            errors=errors or None)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
