# Enterprise Research Skill

**Evidence-grounded company research → single-file interactive HTML reports.**
v2.0 is a **complete rewrite** of v1.x (which produced Markdown + CSV + Excel; see [Releases](https://github.com/maleo0228/enterprise-research-skill/releases) for the archived v1.0.x line).

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

```
research notes → report.json (per data contract) → render.py → report HTML
```

1. Fill in `report.json` following the data contract ([`data-contract/report-data.schema.json`](data-contract/report-data.schema.json)); two validated examples are in [`examples/`](examples/).
2. Render — one command, zero third-party dependencies (Python 3.8+ standard library only):

   ```bash
   python renderer/render.py report.json renderer/skeleton.html report.html
   ```

   The renderer validates the data first (source closure, navigation uniqueness, naming, no hand-written citation marks) and **fails instead of emitting a broken report**.
3. Regression-check layout changes with `renderer/compare.py` (equivalence comparison against a baseline report).

## Repository layout

| Path | Contents |
|---|---|
| `SKILL.md` | Skill entry point (report generation stage) |
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

## License

[MIT](LICENSE)

---

**Note**: the research rulebooks behind the methodology are not part of this public repository; this repo ships the report renderer, the data contract, and finished samples.
