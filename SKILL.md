---
name: enterprise-research-skill
description: Turn a completed company-research dataset (report.json) into a validated, single-file, interactive HTML report. Use when the user has research data conforming to the report-data contract and wants a finished offline HTML report with navigation, search, charts, source traceability, and Markdown export. This skill covers the report generation stage only — the research itself is performed by the user's own research workflow.
---

# Enterprise Research Skill — Report Generation Stage

Render a company-research dataset into a single-file, offline-capable HTML report.

## What this skill does

- Validates a `report.json` against business rules (source closure: every citation declared and used; unique navigation anchors; required naming; no hand-written citation marks). **Validation failure aborts rendering — no broken report is emitted.**
- Renders the validated data into a self-contained HTML page: five modules (Company Overview / Events & Signals / Business & Technology Analysis / IT Focus & Follow-up / Source Index & Evidence Chain), sidebar navigation, full-text search, charts, per-section and full-report Markdown export.
- Everything runs on the Python 3.8+ standard library. No third-party packages, no network, no build step.

## Input contract

The input MUST be a JSON file conforming to [`data-contract/report-data.schema.json`](data-contract/report-data.schema.json). Two validated examples are provided in [`examples/`](examples/):

- `examples/ginlong-solis_report-data_v0.1.json`
- `examples/mingshi-investment_report-data_v0.1.json`

If the user's research output does not yet conform to the contract, reshape it first; do not patch the renderer to accept non-conformant data.

## How to render

```bash
python renderer/render.py <report.json> renderer/skeleton.html <output.html>
```

Then hand the output HTML to the user — it opens directly in any browser, works offline, and can be shared as a single file.

## Regression checking (only when modifying the renderer or skeleton)

```bash
python renderer/compare.py <rendered.html> <baseline.html>
```

Equivalence comparison: verbatim text, source sets per page, chart labels (not coordinates), plus registered baseline normalizations.

## Boundaries

- This skill performs **no research**. Collecting sources, verifying facts, and filling the dataset are the responsibility of the user's own research process.
- `renderer/skeleton.html` is a frozen artifact. Layout changes require a deliberate skeleton-freezing cycle (`make_skeleton.py` documents the procedure), followed by `compare.py` regression against a baseline report.
- Do not commit or transmit internal research notes; only the contract-conformant JSON enters the renderer.
