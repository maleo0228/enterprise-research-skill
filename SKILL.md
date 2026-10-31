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

## Financial block types (overview.financial.blocks)

Supported `type` values:

| type | use for | caption |
|---|---|---|
| `table` | structured figures | required, `表N｜…` |
| `chart_bar` | year/period series (negatives supported since renderer v0.2) | required, `图N｜…` |
| `timeline` | dated event sequences (financing rounds, milestones) | required, `图N｜…` |
| `text` | free-form multi-paragraph blocks | no numbering |
| `missing` | explicit data-gap placeholder | — |

## Research-stage checklist (reference — upstream of this skill)

This skill performs no research (see Boundaries). The checklist below documents, in a tool-neutral form, the research discipline expected of the upstream workflow that produces a contract-conformant `report.json`. It is reference material only. The full frozen spec — research-stage output formats (source list / fact card / gap list), retrieval discipline, and the pre-delivery self-check list — is in [`research-discipline-spec.md`](research-discipline-spec.md) (v0.3, frozen).

1. **Subject lock + name-mapping chain.** Lock the exact legal entity first, then build the chain: given name → brand/product name → official domain → platform namespaces (organization/user names — usually the brand lowercased or the domain stem, e.g. `example.ai` → `github.com/example`, `huggingface.co/example`). Query each candidate namespace **directly**, then verify identity before attributing anything: org name matches domain stem; repo/model content matches the company's business; multiple platforms cross-link. At least two of three checks must pass, else mark "possible name collision, unconfirmed". For non-Latin subjects, cover full-width/half-width and kana variants (e.g. a Latin brand registered as full-width katakana in official filings — search all script variants of the same name).
2. **Platform-direct checklist by subject type.** Prefer direct page fetches over search-engine site filters (unreliable). Technical subjects: GitHub org/repos → Hugging Face org/models → package registries → preprint servers → leaderboards (note overall vs sub-collection ranking calibers). Japan-based subjects: National Tax Agency corporate number publication (full-width name forms; web API requires a registered ID) → EDINET → Wantedly → PR TIMES → industry press → official social accounts. Listed subjects: exchange disclosure portals (A-share/HK/US) → company IR pages.
3. **One-hop diffusion from the official site.** A homepage fetch alone is not "website checked": check sitemap/subpages (sitemap returning the homepage itself = single-page site), footer external links (many tech companies link their GitHub org in the footer), contact channels (mailto / form / same-domain email as domain self-proof), second-domain variants (brand + common TLDs, e.g. .com/.ai/.io — one direct fetch to confirm or falsify), and cross-domain consistency (two domains stating the same facts corroborate each other; conflicts get flagged, not silently picked over).
4. **Recursive diffusion.** From a platform page, walk org → repos → members → related pages until a natural endpoint (e.g. "no public members"); attribute unverified leads as leads, never as facts.
5. **Counter-evidence first.** For every company self-reported claim (performance, quality), actively seek third-party reproductions. Indirect evidence (same technique, same hardware class, different product) may be cited only as ecosystem-level circumstantial evidence, explicitly marked "not a direct test of this product".
6. **Zero-result discipline.** Never assert exhaustive negatives ("no footprint on the internet"). Standard phrasing: "not indexed in public search (channels named); pending platform-direct confirmation", with the evidence trio: channels used / actions taken (keywords + direct queries) / execution date. Only after platform-direct checks also return nothing may "not available via public channels" be stated, listing the checks performed.
7. **Caliber pairing.** Company self-reported figures and third-party measurements are presented side by side, each labeled; leaderboard overall-ranking vs sub-collection calibers are distinguished.

## Delivery checklist

1. `python renderer/test_renderer.py` — attack-surface & regression suite (105 items) must pass; `python renderer/fuzz_renderer.py` (seeded fuzz, 4 seeds × 2000 cases) must report zero defects. Both are release gates for any renderer-related change.
2. `python renderer/check_urls.py report.json` — every source URL reachable; manually re-check any flagged 403/202 (anti-crawler/JS pages may still open in a browser).
3. Open the HTML once in a browser: navigation, search, MD export, charts render.
4. Confirm no *renderer-residual* `{{...}}` tokens in the output — i.e. tokens the renderer failed to substitute. Literal template tokens coming from your own data values are kept verbatim by design (single-pass substitution, renderer v0.10+) and are not a defect; the regression suite's no-residual-token check covers the renderer side.

## Regression checking (only when modifying the renderer or skeleton)

```bash
python renderer/compare.py <rendered.html> <baseline.html>
```

Equivalence comparison: verbatim text, source sets per page, chart labels (not coordinates), plus registered baseline normalizations.

## Boundaries

- This skill performs **no research**. Collecting sources, verifying facts, and filling the dataset are the responsibility of the user's own research process.
- `renderer/skeleton.html` is a frozen artifact. Layout changes require a deliberate skeleton-freezing cycle (`make_skeleton.py` documents the procedure), followed by `compare.py` regression against a baseline report.
- Do not commit or transmit internal research notes; only the contract-conformant JSON enters the renderer.
