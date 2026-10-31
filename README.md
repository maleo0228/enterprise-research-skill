# Enterprise Research Skill

**Evidence-grounded company research → single-file interactive HTML reports.**
**Current version: v2.3.1** · [Changelog](https://github.com/maleo0228/enterprise-research-skill/releases)
v2.0 is a **complete rewrite** of v1.x (which produced Markdown + CSV + Excel; see [Releases](https://github.com/maleo0228/enterprise-research-skill/releases) for the archived v1.0.x line).

## What's new in v2.3.1

- **Research discipline spec added.** New [`research-discipline-spec.md`](research-discipline-spec.md) — a frozen (v0.3), tool-neutral reference for the *research stage* upstream of this skill: the three research-output formats (source list / fact card / gap list), retrieval discipline (subject lock & name-mapping chain, platform-direct checks by subject type, one-hop diffusion from the official site, recursive diffusion, counter-evidence first, zero-result discipline, caliber pairing), and a pre-delivery self-check list. The renderer, contract, and samples are unchanged in scope; this spec makes research-stage outputs auditable instead of free-form.
- **Renderer hardening** (no output changes for conformant data): byte-exact deterministic output (UTF-8/LF on all platforms), GBK-console-safe test suite, and one validation gap closed (deeply nested mechanism fields are now rejected cleanly instead of producing orphan source rows).
- **Test suite**: 105 items + seeded fuzz gate (4 seeds × 2000 cases, zero defects).

## What it does

Research a named company from public sources, then deliver a **single-file, offline-capable HTML report** with:

- **1.0 Company Overview** — profile, ownership, full financials with charts;
- **2.0 Events & Signals** — sourced business events and ranked signals;
- **3.0 Business & Technology Analysis** — mechanism-by-mechanism breakdown, with "confirmed vs. unconfirmed" explicitly separated;
- **4.0 IT Focus & Follow-up** — IT-relevant directions with evidence strength and follow-up suggestions;
- **5.0 Source Index & Evidence Chain** — every claim traceable to a numbered, linked source.

Reports are navigable, searchable, and exportable to Markdown from the page (per-section and full report).

## Sample report

Open the sample directly in your browser — no server needed:

- **Ginlong (Solis) Technologies 锦浪科技** — [ginlong-solis_2026-10-19.html](https://maleo0228.github.io/enterprise-research-skill/samples/ginlong-solis_2026-10-19.html)

## How it works

This repo covers the **report generation stage** only: your research produces a dataset, the renderer turns it into the report. Three steps:

```
your research  →  report.json (conform to the data contract)  →  render.py  →  report.html
```

**1. Prepare the dataset.** Structure your research findings into one `report.json` conforming to [`data-contract/report-data.schema.json`](data-contract/report-data.schema.json). Two validated examples ([`examples/`](examples/)) show the full shape: five modules, a numbered source table, and per-claim `sources` arrays. Hard rules enforced by the contract:

- **Source closure** — every claim is cited as `[E#]`, every `[E#]` is declared in the source table, and every declared source is actually cited. Nothing is traceable to nothing.
- **Citations are generated, never hand-written** — you supply `sources` arrays; the renderer emits the `[E#]` marks. Hand-written citation markup is rejected.
- **Named financial blocks** — financial content is typed blocks (`table` / `chart_bar` / `timeline` / `text` / `missing`), each with a `表N｜` or `图N｜` caption; gaps are declared explicitly with `missing`, never silently dropped.

If your data doesn't fit the contract, reshape the data — do not patch the renderer to accept non-conformant input.

**2. Render.** One command; zero third-party dependencies (Python 3.8+ standard library only, no network, no build step):

```bash
python renderer/render.py report.json renderer/skeleton.html report.html
```

`render.py` validates first — structural completeness, source closure, unique navigation anchors, naming, chart data sanity — and **aborts with a plain, itemized "validation failed" list instead of emitting a broken report**. On success it fills the frozen `skeleton.html` and produces a fully self-contained page: sidebar navigation, full-text search, SVG charts (negative values supported), clickable `[E#]` anchors jumping to the source table, and per-section plus full-report Markdown export.

**3. Verify before delivery.**

```bash
python renderer/check_urls.py report.json   # every source URL reachable; manually re-check any 403/202 flags
```

Then open the HTML once in a browser (navigation, search, MD export, charts) and confirm no leftover `{{...}}` tokens.

**For maintainers** (renderer or skeleton changes only): `python renderer/test_renderer.py` runs the 105-item attack-surface & regression suite, and a mandatory seeded fuzz run (`python renderer/fuzz_renderer.py`, 4 seeds × 2000 cases, zero defects required) — all green before any release; `python renderer/compare.py <rendered.html> <baseline.html>` checks equivalence against a frozen baseline sample.

## Repository layout

| Path | Contents |
|---|---|
| `SKILL.md` | Skill entry point (report generation stage) |
| `research-discipline-spec.md` | Frozen v0.3 research-stage discipline & output-format reference (tool-neutral) |
| `samples/` | Finished single-file HTML report samples (open offline, share freely) |
| `renderer/` | `render.py`, `skeleton.html` (frozen page skeleton), `compare.py`, `make_skeleton.py` |
| `data-contract/` | `report-data.schema.json` — the JSON data contract |
| `examples/` | Two validated example data files (Mingshi / Ginlong) |

## Installation

The repository is a standard agent skill package (entry: `SKILL.md`). Copy or clone it into your agent's skill directory:

```bash
git clone https://github.com/maleo0228/enterprise-research-skill.git
```

- **Codex**: copy to `~/.agents/skills/enterprise-research-skill/` (or `~/.codex/skills/`)
- **Claude Code**: copy to `~/.claude/skills/enterprise-research-skill/`
- **WorkBuddy / CodeBuddy**: copy to `.codebuddy/skills/enterprise-research-skill/` in your project (or import via the GUI skill manager)
- **Kimi / other agents**: point the skill search path at this directory; if the platform does not auto-discover skills, read `SKILL.md` directly and run the render command manually — the renderer is a zero-dependency CLI (Python 3.8+ stdlib) and works standalone.

After installing, restart or refresh the agent so it re-discovers skills.

**Scope note**: this skill covers the *report generation* stage (contract-conformant JSON → validated HTML report). The research stage that produces the dataset is performed by your own research workflow.

## Roadmap

- **Non-IT industry example** — within 3 months of v2.3.1, a manufacturing or consumer-sector listed-company example (full real research, then instantiated to the contract) will be added, shipping with a follow-up release (planned v2.4.0). Progress is tracked in the changelog.

## License

[MIT](LICENSE)

---

**Note**: this repo ships the report renderer, the data contract, the research-discipline spec (v0.3), and finished samples. The analytical frameworks behind the methodology — module design rationale, mechanism-analysis perspectives, direction-rating criteria, inclusion thresholds, and the internal case library — are not part of this public repository.
