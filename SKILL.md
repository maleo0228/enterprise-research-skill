---
name: enterprise-company-research
description: Research one named company from public sources and produce a source-backed Markdown report, a 43-field UTF-8 BOM CSV, and a five-sheet XLSX workbook. Use for company research, not batch scanning or lead discovery.
metadata:
  version: "1.0.1"
---

# Enterprise Research Skill v1.0.1

Research one user-named company. Default to `standard` research and follow this flow:

```text
company input → entity identification → Plan → Research → Verify → Synthesize → Markdown + CSV + five-sheet XLSX
```

Do not perform multi-agent work, batch scanning, ICP/lead discovery, database/API/MCP/Web UI work, complex scoring, PPT, or PDF generation.

## Read before research

1. [research-method.md](references/research-method.md)
2. [company-profile-fields.md](references/company-profile-fields.md)
3. [sources-and-evidence.md](references/sources-and-evidence.md)
4. [company-profile-template.csv](templates/company-profile-template.csv)
5. [workbook-template-guide.md](templates/workbook-template-guide.md)

Read `five-sheet-workbook-template.xlsx` before generating the workbook. All outputs must use the same fact IDs, dates, figures, evidence IDs, and conclusions.

## Rules

- Confirm the legal/standard company name, official site, headquarters, and listed or registered entity. Stop for clarification if entities are ambiguous.
- Prefer official company disclosures, exchanges, regulators, governments, courts, and official sanctions/export-control sources. Search snippets and reposts are leads, not sufficient proof for high-impact facts.
- Use `未发现可靠公开信息` (no reliable public information found), `待核实` (needs verification), or `不适用` (not applicable) instead of guessing.
- Clearly mark every analysis with `分析判断：`; do not present inference, industry convention, or company promotion as independently verified fact.
- Standard research checks compliance, litigation, and penalties. An inaccessible database is a limitation, never proof that no issue exists.

## Outputs

1. `{company}_企业研究_V1.0.md` — detailed evidence, scope, conflicts, repeat-record tables, and limitations.
2. `{company}_企业结构化数据_V1.0.csv` — 14 columns, 43 field rows, UTF-8 BOM, comma-separated, CRLF. It is the structured-data attachment for machine reading, imports, comparison, and completeness checks. Chinese headings are retained intentionally for the approved Chinese Excel workflow.
3. `{company}_企业画像_V1.0.xlsx` — five visible sheets in this fixed order: `企业总览`, `业务·产品·技术`, `发展·资本·市场`, `研究判断·IT机会·证据`, `来源索引`.

The first four sheets show short source names and evidence IDs only. The fifth sheet holds complete URLs and the field-level evidence ledger. Do not silently omit XLSX; state why if the environment cannot generate it.

**No-freeze-pane rule (v1.0.1):** do not set frozen panes on any of the five sheets. Do not use a data-header row, narrative boundary, or any cell as a freeze point. After generation, inspect the workbook package itself: no worksheet may contain `state="frozen"`. A rendered image alone is not enough to pass this check.

## Invocation

```text
Use enterprise-company-research to perform standard research on "宁德时代" and write the outputs to 测试结果.
```
