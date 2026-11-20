---
name: enterprise-research-skill
description: Research a company from public sources and deliver a validated, single-file, interactive HTML report. Use when the user asks to analyze/research a company or already has research data (report.json) conforming to the report-data contract and wants a finished offline HTML report with navigation, search, charts, source traceability, and Markdown export. Covers both stages — research discipline (governed by research-discipline-spec.md) and validated rendering.
---

# Enterprise Research Skill

Two stages: research a company from public sources into a contract-conformant dataset, then render that dataset into a single-file, offline-capable HTML report.

## Two-stage workflow

1. **Research stage** — collect and verify sources per [`research-discipline-spec.md`](research-discipline-spec.md), then assemble a contract-conformant `report.json`. Every delivery starts here unless the user already supplies a conformant `report.json`.
2. **Rendering stage** — validate the dataset against the contract and render it into the single-file HTML report described below.

## What this skill does

- Validates a `report.json` against business rules (source closure: every citation declared and used; unique navigation anchors; required naming; no hand-written citation marks). **Validation failure aborts rendering — no broken report is emitted.**
- Renders the validated data into a self-contained HTML page: five modules (Company Overview / Events & Signals / Business & Technology Analysis / IT Focus & Follow-up / Source Index & Evidence Chain), sidebar navigation, full-text search, charts, per-section and full-report Markdown export.
- Everything runs on the Python 3.8+ standard library. No third-party packages, no network, no build step.

## Input contract

The input MUST be a JSON file conforming to [`data-contract/report-data.schema.json`](data-contract/report-data.schema.json). Two validated examples are provided in [`examples/`](examples/):

- `examples/ginlong-solis_report-data_v0.1.json`
- `examples/mingshi-investment_report-data_v0.1.json`

If the user's research output does not yet conform to the contract, reshape it first; do not patch the renderer to accept non-conformant data.

Starting from scratch? [`templates/report-skeleton.json`](templates/report-skeleton.json) is an all-placeholder skeleton covering every field (fill in values; keep the first 8 `basic_info` labels untouched). [`templates/gap-list-skeleton.json`](templates/gap-list-skeleton.json) shows the gap-list format for the delivery gate. `templates/report-filled-fixture.json` (same shape, fully filled with obviously fictional 占位- placeholders) exists only for regression testing — do not copy its values into a real report.

## Contract pitfalls (the four that cause rework)

Field experience: nearly all first-pass rework falls into one of these four. Run the pre-check below while writing — it reuses the renderer's own `validate()`, so what it reports is exactly what delivery-time validation will enforce.

1. **basic_info core order.** The first 8 items of `overview.basic_info` are a closed core list and must appear in exact order: 公司全称 / 官网 / 成立时间 / 注册地／经营地 / 所有制／资本状态 / 高管背景 / 员工规模 / 组织结构. Extensions (registered capital, credit code, …) may only be appended after item 8.
2. **No mixing annual and interim figures in one table or chart.** Annual tables/charts carry complete fiscal years only; interim/cumulative periods (2026H1, Q3, TTM, …) go in a separate "latest reporting period (cumulative)" table. See spec §5.2.1.
3. **Never hand-write citation marks.** Do not type `[E1]` or `(E2)` in any text or note field — citations are generated from `sources` arrays. Hand-written marks are rejected tree-wide (`scan_sup`).
4. **URL reachability has a standard handling path.** A source whose URL fails reachability at delivery time is handled per the delivery checklist (research-stage re-verification first; environment limits are never written into identity fields and never reported as "undisclosed"). Do not improvise a different handling.

Pre-check while writing (seconds, no rendering, no gap gate):

```bash
python renderer/render.py <report.json> --check-only
```

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

## Research-stage checklist (mandatory)

Every delivery produced with this skill starts here. The checklist below summarizes, in a tool-neutral form, the research discipline for producing a contract-conformant `report.json`. The full frozen spec — research-stage output formats (source list / fact card / gap list), retrieval discipline, the collection-dimension → contract mapping (§10), the neutral defaults (§11), and the pre-delivery self-check list — is in [`research-discipline-spec.md`](research-discipline-spec.md) (v0.6, frozen). **Read it in full before the research stage begins.**

1. **Subject lock + name-mapping chain.** Lock the exact legal entity first, then build the chain: given name → brand/product name → official domain → platform namespaces (organization/user names — usually the brand lowercased or the domain stem, e.g. `example.ai` → `github.com/example`, `huggingface.co/example`). Query each candidate namespace **directly**, then verify identity before attributing anything: org name matches domain stem; repo/model content matches the company's business; multiple platforms cross-link. At least two of three checks must pass, else mark "possible name collision, unconfirmed". For non-Latin subjects, cover full-width/half-width and kana variants (e.g. a Latin brand registered as full-width katakana in official filings — search all script variants of the same name).
2. **Platform-direct checklist by subject type.** Prefer direct page fetches over search-engine site filters (unreliable). Technical subjects: GitHub org/repos → Hugging Face org/models → package registries → preprint servers → leaderboards (note overall vs sub-collection ranking calibers). Japan-based subjects: National Tax Agency corporate number publication (full-width name forms; web API requires a registered ID) → EDINET → Wantedly → PR TIMES → industry press → official social accounts. Listed subjects: exchange disclosure portals (A-share/HK/US) → company IR pages → exchange investor Q&A platforms. Mainland-China unlisted subjects: national enterprise credit publicity system → ICP filing lookup → tender/award notices (government procurement and public-resource trading platforms) → official job postings (JDs reveal systems in use) → patent/software-copyright records; commercial registry aggregators are often geo-blocked abroad — re-check per spec §1.3, never record as "does not exist".
3. **One-hop diffusion from the official site.** A homepage fetch alone is not "website checked": check sitemap/subpages (sitemap returning the homepage itself = single-page site), footer external links (many tech companies link their GitHub org in the footer), contact channels (mailto / form / same-domain email as domain self-proof), second-domain variants (brand + common TLDs, e.g. .com/.ai/.io — one direct fetch to confirm or falsify), and cross-domain consistency (two domains stating the same facts corroborate each other; conflicts get flagged, not silently picked over).
4. **Recursive diffusion.** From a platform page, walk org → repos → members → related pages until a natural endpoint (e.g. "no public members"); attribute unverified leads as leads, never as facts.
5. **Counter-evidence first.** For every company self-reported claim (performance, quality), actively seek third-party reproductions. Indirect evidence (same technique, same hardware class, different product) may be cited only as ecosystem-level circumstantial evidence, explicitly marked "not a direct test of this product".
6. **Zero-result discipline.** Never assert exhaustive negatives ("no footprint on the internet"). Standard phrasing: "not indexed in public search (channels named); pending platform-direct confirmation", with the evidence trio: channels used / actions taken (keywords + direct queries) / execution date. Only after platform-direct checks also return nothing may "not available via public channels" be stated, listing the checks performed.
7. **Caliber pairing.** Company self-reported figures and third-party measurements are presented side by side, each labeled; leaderboard overall-ranking vs sub-collection calibers are distinguished.
8. **Neutral defaults.** When the user specifies no parameters (purpose / depth / angle / market / deadline), apply the spec §11 neutral defaults and execute end-to-end to a first version — at most 2 blocking questions; non-blocking choices follow the defaults and are stated on the report's first screen. Never hard-code deployment-specific scenario defaults into the report.
9. **Missing-block brevity.** A `missing` note is a one-line summary plus a `\n`-separated compact enumeration (≤6 lines total, one sentence per item); long reasons and impacts belong in `gap-list.json`. The spec §11 neutral-default one-liner must describe what was actually executed — example phrasings are not fixed boilerplate.

## Delivery checklist

1. **[Renderer/skeleton changes only]** `python renderer/test_renderer.py` — attack-surface & regression suite (158 items) must pass; `python renderer/fuzz_renderer.py --cases 2000 --seed S` for S in 20261022, 1, 777, 42 (seeded fuzz, 4 seeds × 2000 cases) must report zero defects. Both are release gates for any renderer-related change — skip for routine report deliveries (they do not modify the renderer).
2. `python renderer/check_urls.py report.json` — every source URL reachable; manually re-check every `WARN` (403/202/429, cross-site redirect, timeout, TLS interrupted, or http-only links blocked by the network — anti-crawler/JS pages may still open in a browser). TLS certificates are verified by default; `--insecure` is for comparison only. Sites that reject generic clients (e.g. SEC EDGAR returns 403) need `--user-agent "Name email@example.com"`. **URLs already fetched successfully during research (the `fetched` field is the record): a delivery-time `WARN` is re-checked once with a second method (`-k` / browser UA / WebFetch / mirror); if the re-check passes, keep the primary URL and note the actual access path in the source/caliber column — never swap links on WARN alone; replace only confirmed-dead links.** Environmental constraints go in the source/caliber column, never the `identity` field. For due-diligence deliveries also run `render.py … --strict` so contract warnings (date/URL format, uncited 4.0 items) fail the build.
3. `python renderer/gap_fidelity_check.py gap-list.json report.json` — every research-stage gap (spec §7.3, machine form) maps to a carrier in the report (financial `missing` block, annotated `basic_info` row, or an on-report declaration), resolved gaps cite a used source, and no financial `missing` block is orphaned; `--strict` for due-diligence deliveries. Run after the gap list and `report.json` both exist, before rendering. **Deliverable renders gate on the gap check in one step: `python renderer/render.py report.json skeleton.html out.html --gap-list gap-list.json` (the gate runs after validation and before rendering — failure means no output file, no delivery). Seeing `GAP-GATE-SKIPPED:` on stderr in non-delivery contexts (batch re-render, re-validation of old drafts, `--check-only` pre-checks) is expected — not an error, do not rework.**
4. `render.py` must finish with **zero validation warnings (校验警告)**. A warning means the data violates the spec — mixed annual/interim periods (§5.2.1), date/URL format, uncited 4.0 items — and is never cosmetic: fix `report.json` and re-render until clean. **Never deliver a report that carries warnings.** For due-diligence deliveries run `render.py … --strict` so any warning fails the build.
5. Open the HTML once in a browser: navigation, search, MD export, charts render.
6. Confirm no *renderer-residual* `{{...}}` tokens in the output — i.e. tokens the renderer failed to substitute. Literal template tokens coming from your own data values are kept verbatim by design (single-pass substitution, renderer v0.10+) and are not a defect; the regression suite's no-residual-token check covers the renderer side.

## Regression checking (only when modifying the renderer or skeleton)

```bash
python renderer/compare.py <rendered.html> <baseline.html>
```

Equivalence comparison: verbatim text, source sets per page, chart labels (not coordinates), plus registered baseline normalizations.

## Boundaries

- **Two-stage scope.** This skill covers the research stage (governed by `research-discipline-spec.md`) and the rendering stage. Research discipline is mandatory; the renderer validates and renders its output. When invoked without an existing `report.json`, start at the research stage — do not stop at rendering.
- `renderer/skeleton.html` is a frozen artifact. Layout changes require a deliberate skeleton-freezing cycle (`make_skeleton.py` documents the procedure), followed by `compare.py` regression against a baseline report.
- Do not commit or transmit internal research notes; only the contract-conformant JSON enters the renderer.
