# Sources and evidence rules

## Source priority

| Level | Sources | Typical use |
|---|---|---|
| A | Official company/IR, original reports, exchanges, regulators, governments, courts, official sanctions/export-control databases | financials, ownership, listing, penalties, litigation, formal policy |
| B | Official press releases/social posts, authoritative associations or original research reports | product, milestones, statistics context |
| C | High-quality mainstream media | independent context |
| D | Trade media, database summaries, reposts, search snippets | leads or limited evidence only |

High-impact statements must preferentially use direct Level A disclosure. A mirror, repost, or search result cannot alone be called verified.

## Definitions

- **Fact**: an objectively stated item traceable to a source, with publication date, access date, and cutoff date.
- **Calculation**: derived from stated figures; show formula and period.
- **Analysis judgment**: begin with `分析判断：`, state evidence, conditions, and uncertainty.
- **Verified**: direct primary support or two independent reliable sources aligned on entity, time, and scope.
- **Limited evidence**: a source exists but scope, timeliness, independence, or definition is insufficient.
- **Needs verification**: conflicting or unclear source/entity/scope.
- **No reliable public information found**: a transparent search result, not proof of nonexistence.

## Mandatory checks

For standard research, verify entity identity; finance and capital-market facts; market and customer evidence; and compliance/litigation/penalties, including relevant official sanctions/export-control entry points. Record search date, names searched, public results, coverage limits, and inaccessible sources.

## Output rules

Each CSV row should contain content, status, confidence, source, URL, publication date, access date, cutoff date, and a note where needed. Keep at most two URLs in CSV; retain full source detail, conflicts, and calculations in Markdown and the workbook source index. Do not leave unexplained blanks.

`{company}_企业结构化数据_V1.0.csv` is the structured-data attachment. `{company}_企业研究_V1.0.md` and `{company}_企业画像_V1.0.xlsx` are the primary reading outputs. The workbook must have five visible sheets and no frozen panes: inspect the worksheet XML and confirm no pane has `state="frozen"`.
