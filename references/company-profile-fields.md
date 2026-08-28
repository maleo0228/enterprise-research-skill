# Company profile field contract

The CSV has 14 columns and 43 field rows. Empty values must be explicit: `未发现可靠公开信息`, `待核实`, or `不适用`.

| Fields | Group | Information type |
|---|---|---|
| 1–6 | Research metadata: input name, standard name, short name, English name, research date, cutoff date | fact |
| 7–15 | Identity and governance: site, founding, headquarters, ownership/control, leadership, capital-market status, funding/shareholders, stage, organization signals | fact / judgment |
| 16–20 | Industry environment: primary market, segment/use case, market-cycle evidence, policy/regulation, trends/drivers | fact / judgment |
| 21–27 | Business ecosystem: products, delivery model, value proposition/customer type, revenue mix, value chain, representative customers/coverage, milestones/recent events | fact / judgment |
| 28–33 | Operations and finance: three-year figures, revenue trend, profitability, operating cash flow, anomalies, financial-health judgment | fact / calculation / judgment |
| 34–38 | Technology, competition, compliance: architecture, position/share, competitors, differentiation, compliance/litigation/penalties check | fact / judgment |
| 39–43 | Conclusions and boundaries: risks, indicators, 1–3 year conditional outlook, evidence gaps/conflicts, one-line profile | judgment |

## Repeat-record structures

Use rows, not product1/product2/product3 fields, for:

- products: ID, name, category, use case, customer, maturity, commercialization, release/version, differentiation, evidence ID;
- technical capabilities: ID, dimension, applicability, level, fact basis, evidence ID;
- customers/cases: ID, customer type/industry, named customer only if public, product/use case, date, signal, evidence ID;
- events: ID, date, type, importance, fact, business/IT impact judgment, evidence ID;
- competitors: ID, company, comparison dimension, public evidence, relative difference, limitation, evidence ID;
- ratings: ID, dimension, level, fact ID, basis, applicability;
- IT opportunities: ID, dimension, level, demand status, trigger, window, fact ID, action, applicability;
- evidence ledger: ID, fact, source level/name/URL/dates, official status, cross-check, linked conclusion;
- fact–judgment–opportunity map: IDs, relationship statement, evidence ID.

KPI cards, data completeness, product count, attention level, and overall IT rating are display-derived items, not new source fields. AI/GPU/RAG/Agent items are included only when applicable and evidenced.
