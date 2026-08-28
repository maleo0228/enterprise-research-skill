# Enterprise Research Skill V1.0.0

An evidence-first skill for researching one named company from public information. It identifies the entity, plans the research, verifies high-impact claims, and produces one detailed report plus structured CSV and Excel outputs.

## What it is for

- A single, user-specified company.
- Public-source research with clear evidence, date, and scope.
- A 43-field summary plus repeatable product, customer/case, event, competitor, score, IT-opportunity, evidence, and fact-to-judgment-to-opportunity records.

It is not for multi-agent workflows, batch scanning, ICP or lead discovery, databases, APIs, MCP, Web UI, complex scoring, PPT, or PDF. It is not legal, financial, investment, or compliance advice.

## Research flow

```text
Entity identification → Plan → Research → Verify → Synthesize
```

High-impact facts should use primary public sources first: official company/IR materials, original filings, exchanges, regulators, governments, courts, and official sanctions/export-control databases. If a fact cannot be verified, the skill says so rather than guessing. Facts, calculations, analysis judgments, and opportunity judgments are explicitly separated.

## Outputs

| File | Purpose |
|---|---|
| `{company}_企业研究_V1.0.md` | Detailed research, evidence ledger, conflicts, reasoning, repeat-record tables, and limitations. |
| `{company}_企业画像_V1.0.csv` | 14 columns and 43 field rows. UTF-8 BOM and CRLF for Chinese Excel compatibility. |
| `{company}_企业画像_四页_V1.0.xlsx` | A five-sheet workbook: four analysis pages plus the source index. |

The workbook sheets are fixed: `企业总览`, `业务·产品·技术`, `发展·资本·市场`, `研究判断·IT机会·证据`, `来源索引`. The Chinese output labels are intentional: they preserve the approved Excel reading workflow. CSV is the compact exchange format; the workbook retains layout, wrapping, filtering, frozen panes, and source drill-down.

## Codex

G4 has verified local Codex installation, discovery, reference/template reading, a minimal official-site lookup, and generation of all three output types. Give Codex network access and write access to the selected output directory.

Example:

```text
Use enterprise-company-research to perform standard research on "宁德时代" and write the outputs to 测试结果.
```

## WorkBuddy installation

WorkBuddy support is **compatibility-designed, not yet device-tested**. After the GitHub Release is published, download the dedicated release ZIP; in WorkBuddy choose **Skills → Add skill → Upload skill**, select the ZIP, then enable it. Do not use GitHub source-code ZIPs. A GitHub URL is not a confirmed direct-install method.

Minimum test prompt:

```text
使用企业研究Skill对宁德时代做一次快速研究，先确认主体，再输出可追溯来源。
```

Grant only the network and selected output-folder permissions needed for this research.

## Compatibility with the previous 40 fields

The approved CSV contract has 43 summary fields. The prior standard-name field is represented by fields 2–4 (standard name, short name, English name where available); the former combined founding/headquarters field is split into fields 8–9. Other semantics are preserved; see [company-profile-fields.md](references/company-profile-fields.md).

## Known limitations

- CSV display and delimiter behavior vary by local Excel settings; the workbook is the primary reading surface.
- The G3 workbook still needs human opening checks in Mac/Windows Excel.
- WorkBuddy import, trigger, network access, and three-output generation will be validated from the public Release in G7.

## Acknowledgements and license

The project structure and research method reference [flicy/enterprise-company-research-agent](https://github.com/flicy/enterprise-company-research-agent). It borrows only the Plan → Research → Synthesize, Quick Research, CSV, and anti-hallucination ideas from Browserbase company-research. Both references are MIT licensed. Browserbase API, API keys, CLI, and complex subagents are not included.

Released under the [MIT License](LICENSE).
