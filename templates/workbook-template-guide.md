# Five-sheet workbook guide (v1.0.1)

Use `five-sheet-workbook-template.xlsx` as the formal output template. It has four topic sheets and one source index, in this fixed order:

1. `企业总览`
2. `业务·产品·技术`
3. `发展·资本·市场`
4. `研究判断·IT机会·证据`
5. `来源索引`

## Mandatory compatibility rule

Do **not** set frozen panes on any of the five worksheets. A data-table header is not a freeze point. After producing a workbook, inspect the worksheet XML and reject output if any pane has `state="frozen"`; visual rendering is supplementary only.

Build the 43 summary fields and evidence/fact IDs first. The first three sheets show compact facts, cards, matrices, and timelines. Sheet4 shows judgments, ratings, opportunities, mappings, and a concise set of key evidence. Sheet5 holds the complete field-level source index: field number, category, field, source, URL, publication date, access date, cutoff date, evidence/fact IDs, source level, official status, cross-check, status, and limitations.

Do not put long URLs on the first four sheets. Sheet4 key evidence must be a subset of Sheet5 and connect through evidence IDs. Use repeat-record rows for products, customers, events, competitors, ratings, opportunities, and mappings. Do not invent example data or force inapplicable IT categories.
