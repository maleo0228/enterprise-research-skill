# Enterprise Research Skill

**Evidence-grounded company research → a single-file, offline HTML report.**
**Current version: v2.3.1** · [Changelog](https://github.com/maleo0228/enterprise-research-skill/releases) · [中文版 README](README.zh-CN.md)

Research a company from public sources, structure the findings as one JSON file, and this skill turns it into a **validated, navigable, fully source-traceable report** — a single HTML file that opens in any browser, works offline, and can be shared as-is. v2.0 is a complete rewrite of the archived [v1.x line](https://github.com/maleo0228/enterprise-research-skill/releases).

> **New in v2.3.1** — the research-stage discipline spec ([see below](#research-discipline--the-stage-before-rendering-new-in-v231)), plus renderer hardening: byte-exact deterministic output (UTF-8/LF on all platforms), GBK-console-safe test suite, one validation gap closed. **Zero output change for conformant data.**

## See it in one minute

Open a finished sample — no server, no install:

- **Ginlong (Solis) Technologies 锦浪科技** — [ginlong-solis_2026-10-19.html](https://maleo0228.github.io/enterprise-research-skill/samples/ginlong-solis_2026-10-19.html)
- **Mingshi Investment 鸣石投资** — [mingshi-investment_2026-10-14.html](https://maleo0228.github.io/enterprise-research-skill/samples/mingshi-investment_2026-10-14.html)

Then render your own:

```bash
python renderer/render.py report.json renderer/skeleton.html report.html
```

That is the whole pipeline: one command, **Python 3.8+ standard library only** — no third-party packages, no network, no build step.

## What you get

A single self-contained HTML report, five modules:

- **1.0 Company Overview** — profile, ownership & financing, full financials with charts;
- **2.0 Events & Signals** — sourced business events, ranked signals;
- **3.0 Business & Technology Analysis** — mechanism-by-mechanism breakdown, with *confirmed* and *unconfirmed* explicitly separated;
- **4.0 IT Focus & Follow-up** — IT-relevant directions graded by evidence strength;
- **5.0 Source Index & Evidence Chain** — every key claim traceable to a numbered source with its original link.

Plus sidebar navigation, full-text search, SVG charts (negative values supported), clickable `[E#]` anchors jumping to the source table, and per-section / full-report Markdown export.

## Research discipline — the stage before rendering (new in v2.3.1)

A report is only as trustworthy as the research behind it. [`research-discipline-spec.md`](research-discipline-spec.md) — frozen v0.3, tool-neutral — defines what disciplined research output looks like, so research notes are **auditable instead of free-form prose**:

- **Three output formats**: source list / fact card / gap list — every number carries a numbered source, every gap is declared with its reason and impact;
- **Retrieval discipline**: lock the exact legal entity first and build the name-mapping chain (given name → brand → domain → platform namespaces); check platforms directly by subject type; diffuse one hop from the official site; recurse from platform pages; seek counter-evidence before trusting self-reported claims; never assert "nothing exists" without the zero-result evidence trio (channels / actions / date); pair self-reported figures with third-party measurements, calibers labeled;
- **A pre-delivery self-check list** (spec §8).

`SKILL.md` carries a condensed 7-point checklist of the same discipline. This skill still performs no research itself — the spec tells your own research workflow what "done" looks like.

## How it works

```
your research → report.json (conform to the data contract) → render.py → report.html
```

**1. Prepare the dataset.** Structure your findings into one `report.json` conforming to [`data-contract/report-data.schema.json`](data-contract/report-data.schema.json). Two validated examples in [`examples/`](examples/) show the full shape: five modules, a numbered source table, per-claim `sources` arrays. Three hard rules enforced by the contract:

- **Source closure** — every claim is cited as `[E#]`, every `[E#]` is declared in the source table, and every declared source is actually cited;
- **Citations are generated, never hand-written** — you supply `sources` arrays; the renderer emits the `[E#]` marks; hand-written citation markup is rejected;
- **Named financial blocks** — financial content is typed blocks (`table` / `chart_bar` / `timeline` / `text` / `missing`), each with a `表N｜` or `图N｜` caption; gaps are declared explicitly with `missing`, never silently dropped.

If your data doesn't fit the contract, reshape the data — do not patch the renderer to accept non-conformant input.

**2. Render.** `render.py` **validates first** — structural completeness, source closure, unique navigation anchors, naming, chart-data sanity — and aborts with a plain, itemized "validation failed" list instead of emitting a broken report. On success it fills the frozen `skeleton.html` and emits the fully self-contained page.

**3. Verify before delivery.**

```bash
python renderer/check_urls.py report.json   # every source URL reachable; WARN items (403/202/429, cross-site redirect, timeout, TLS interrupted, http-only blocked by network) need a manual re-check
```

Then open the HTML once in a browser (navigation, search, MD export, charts) and confirm no *renderer-residual* `{{...}}` tokens — literal template tokens coming from your own data values are kept verbatim by design (single-pass substitution, renderer v0.10+) and are not a defect.

## Repository layout

| Path | Contents |
|---|---|
| `SKILL.md` | Skill entry point (report generation stage) + condensed research-stage checklist |
| `research-discipline-spec.md` | Frozen v0.3 research-stage discipline & output-format reference (tool-neutral) |
| `data-contract/` | `report-data.schema.json` — the JSON data contract |
| `examples/` | Two validated example datasets (Mingshi / Ginlong) |
| `renderer/` | `render.py`, frozen `skeleton.html`, `compare.py`, `check_urls.py`, test & fuzz gates; `make_skeleton.py` (maintainer-only — refuses to run in public checkouts without the internal baseline) |
| `samples/` | Finished single-file HTML report samples (open offline, share freely) |

## Installation

The repository is a standard agent skill package (entry: `SKILL.md`). Clone or copy it into your agent's skill directory:

```bash
git clone https://github.com/maleo0228/enterprise-research-skill.git
```

- **Codex**: copy to `~/.agents/skills/enterprise-research-skill/` (or `~/.codex/skills/`)
- **Claude Code**: copy to `~/.claude/skills/enterprise-research-skill/`
- **WorkBuddy**: copy to `~/.workbuddy/skills/enterprise-research-skill/` (user-level) or `{workspace}/.workbuddy/skills/enterprise-research-skill/` (project-level)
- **Kimi / other agents**: point the skill search path at this directory; if the platform does not auto-discover skills, read `SKILL.md` directly and run the render command manually — the renderer is a zero-dependency CLI (Python 3.8+ stdlib) and works standalone.

After installing, restart or refresh the agent so it re-discovers skills.

**Scope**: this skill covers the *report generation* stage (contract-conformant JSON → validated HTML report). The research stage that produces the dataset is performed by your own research workflow, guided by [`research-discipline-spec.md`](research-discipline-spec.md).

## For maintainers

Renderer or skeleton changes only: `python renderer/test_renderer.py` runs the 116-item attack-surface & regression suite, and a mandatory seeded fuzz run (`python renderer/fuzz_renderer.py`, 4 seeds × 2000 cases, zero defects required) — all green before any release; `python renderer/compare.py <rendered.html> <baseline.html>` checks equivalence against a frozen baseline sample.

## Roadmap

- **Non-IT industry example** — within 3 months of v2.3.1, a manufacturing or consumer-sector listed-company example (full real research, then instantiated to the contract) will be added, shipping with a follow-up release (planned v2.4.0). Progress is tracked in the changelog.

## License

[MIT](LICENSE)

---

**Note**: this repo ships the report renderer, the data contract, the research-discipline spec (v0.3), and finished samples. The analytical frameworks behind the methodology — module design rationale, mechanism-analysis perspectives, direction-rating criteria, inclusion thresholds, and the internal case library — are not part of this public repository.
