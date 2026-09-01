# 企业研究 Skill V1.0.1

这是面向一家指定企业的公开信息研究 Skill。它先确认主体，再完成 Plan、Research、Verify、Synthesize，输出详细研究、43字段 CSV 和五Sheet Excel 工作簿。

## 适用与边界

- 仅研究一家公司；主体不清时要求补充股票代码、国家/地区或官网。
- 重要事实优先官网、原始披露、交易所、监管、政府、法院和官方制裁/出口管制入口。
- 事实、计算、分析判断和机会判断明确分开；无法确认写“待核实”，找不到可靠来源写“未发现可靠公开信息”。

不用于多 Agent、批量研究、ICP/客户发现、数据库、API、MCP、Web UI、复杂评分、PPT 或 PDF；不构成法律、财务、投资或合规意见。

## 调用与输出

```text
请使用 enterprise-company-research，对“宁德时代”执行标准研究，输出到测试结果。
```

默认输出：

1. `{企业名}_企业研究_V1.0.md`：详细证据、口径、冲突和限制；
2. `{企业名}_企业结构化数据_V1.0.csv`：14列、43字段行、UTF-8 BOM、CRLF 的结构化数据附件；
3. `{企业名}_企业画像_V1.0.xlsx`：4个主题页加`来源索引`的五Sheet工作簿。

固定Sheet顺序：`企业总览`、`业务·产品·技术`、`发展·资本·市场`、`研究判断·IT机会·证据`、`来源索引`。前四页只保留短来源名与证据编号，完整 URL 与字段级台账放在最后一页。CSV是机器读取、跨工具导入、企业比较和字段完整性检查用的结构化数据附件；普通用户优先阅读 Markdown 与 XLSX。五个Sheet均不得设置冻结窗格；生成后须检查底层窗格记录不含`state="frozen"`。

## 安装状态

Codex 已完成 G4 最小实测：本地安装、发现、引用读取、联网核验和三类输出均通过。

v1.0.0已完成 WorkBuddy 实机安装、触发和三类文件生成，但生成的XLSX因错误冻结窗格未通过滚动验收。v1.0.1候选版禁止所有Sheet设置冻结窗格，发布后仍需从公开 Release 重新下载验证。请在 WorkBuddy 依次执行“技能 → 添加技能 → 上传技能 → 启用”；GitHub 仓库 URL 不是已验证的直装入口。

## 与旧40字段的关系

正式 CSV 升级为43字段：字段2—4承接旧标准全称/简称/英文名，字段8—9拆分旧成立与总部；其余语义以字段说明为准。CSV是结构化数据附件；五Sheet XLSX保留阅读层级、筛选、换行和来源下钻，五页均不设置冻结窗格。

## 已知限制

- CSV 的分列和显示会受 Excel 地区设置影响；五Sheet XLSX是正式阅读载体。
- G3 工作簿仍待 Mac/Windows Excel 真人打开复核。
- v1.0.1候选版仍待 WorkBuddy、Microsoft Excel 和 WPS 完成真人打开、上下左右滚动、切换Sheet及重新打开验证。
- GitHub补丁版本为v1.0.1；输出文件名中的`V1.0`表示未改变的数据结构版本。

## 致谢与许可

参考`enterprise-company-research-agent`的公开研究流程与结构，并借鉴 Browserbase company-research 的 Plan → Research → Synthesize、Quick Research、CSV 与防无依据结论思想。两者均为 MIT License；未引入 Browserbase API、密钥、CLI 或复杂子代理。

本项目按 [MIT License](LICENSE) 发布。
