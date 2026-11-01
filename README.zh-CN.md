# Enterprise Research Skill｜企业深度研究 Skill

**基于公开证据的企业研究 → 单文件离线 HTML 报告。**
**当前版本：v2.3.3** ·[更新日志](https://github.com/maleo0228/enterprise-research-skill/releases) · [English README](README.md)

对指定企业做公开信息研究，把结论整理成一个 JSON 文件，本 skill 将其变成一份**经校验、可导航、全链路可溯源的报告**——单个 HTML 文件，任何浏览器直接打开、离线可用、可原样转发。v2.0 是对 [v1.x（已归档）](https://github.com/maleo0228/enterprise-research-skill/releases) 的完全重写。

> **v2.3.3 新特性**——图表正确性与可读性全面修复：柱状图不再静默丢弃超过 4 个类目的数据；数值标签、图例、坐标轴不再互相重叠（按实测文字包围盒计算布局）；手机与窄窗口下表格在卡片内横向滚动、图上文字不小于可读的 11px。另有：手写引用编号被拒绝、4.0 方向逐条"未挂来源"警告、链接检查重写（默认校验 TLS、失败给原因、重定向标 WARN、GBK 安全、`--json`）、规范补充中国非上市企业来源平台、两个示例 4.0 全部挂来源、MD 导出附图表数据表。119 项回归套件、种子化模糊零缺陷。≥1000px 桌面渲染与 v2.3.1 逐像素一致。
>
> **v2.3.1 新特性**——研究段纪律规范（[见下文](#研究纪律渲染之前的那一段-v231-新增)），以及渲染器加固：跨平台逐字节确定性输出（统一 UTF-8/LF）、测试套件 GBK 控制台环境可用、封堵一处校验缺口。**合规数据产出零变化。**

## 一分钟看懂

直接打开成品样张——无需服务器、无需安装：

- **锦浪科技（Ginlong/Solis）**——[ginlong-solis_2026-10-19.html](https://maleo0228.github.io/enterprise-research-skill/samples/ginlong-solis_2026-10-19.html)
- **鸣石投资（Mingshi）**——[mingshi-investment_2026-10-14.html](https://maleo0228.github.io/enterprise-research-skill/samples/mingshi-investment_2026-10-14.html)

然后渲染你自己的数据：

```bash
python renderer/render.py report.json renderer/skeleton.html report.html
```

这就是全部流程：一条命令，**仅需 Python 3.8+ 标准库**——零第三方依赖、零网络、零构建。

## 你会得到什么

一个自包含 HTML 报告，五个模块：

- **1.0 企业概览**——基础信息、股权与融资、完整财务数据与图表；
- **2.0 经营事件与信号**——有来源的经营事件与分级信号；
- **3.0 业务及技术解析**——按机制逐条拆解，"已确认／未确认"显式分离；
- **4.0 IT 关注方向及跟进**——按证据强度分级的 IT 方向与跟进建议；
- **5.0 来源索引与证据链**——每个关键结论可回溯到编号来源（含原始链接）。

另含：侧边导航、全文搜索、SVG 图表（支持负值）、可点击跳转来源表的 `[E#]` 锚点、按模块与全文导出 Markdown。

## 研究纪律——渲染之前的那一段（v2.3.1 新增）

报告的可信度取决于背后的研究。[`research-discipline-spec.md`](research-discipline-spec.md)——冻结版 v0.3、工具中立——定义了"规范的研究产物"长什么样，让研究记录**可核验、不再是自由散文**：

- **研究段三格式**：来源清单／事实卡片／缺口清单——每个数字挂编号来源，每个缺口声明原因与影响；
- **检索动作纪律**：先锁定准确法人人名并建立名称映射链（给定名→品牌→域名→平台命名空间）；按标的类型平台直查；官网一跳扩散；从平台页线索递归；公司自述主张先找反方复核；不作无据否定——零结果须留举证三要素（渠道／动作／日期）；公司口径与第三方实测并排呈现、口径标注；
- **交付前自检清单**（规范 §8）。

`SKILL.md` 载有同一套纪律的 7 点浓缩清单。本 skill 本身仍不做研究——规范的作用是告诉您自己的研究工作流"做到什么程度算完成"。

## 工作原理

```
你的研究  →  report.json（按数据契约填写）  →  render.py  →  成品 HTML
```

**1. 准备数据集。** 把研究结论结构化为一个符合 [`data-contract/report-data.schema.json`](data-contract/report-data.schema.json) 的 `report.json`。[`examples/`](examples/) 内有两个通过校验的实例（鸣石／锦浪）展示完整形态。契约三条硬规则：

- **来源闭环**——每条结论以 `[E#]` 引用，每个 `[E#]` 在来源表声明，每个声明的来源都被实际引用；
- **引用标记由渲染器生成，禁止手写**——数据只提供 `sources` 数组，手写引用标记会被拒绝；
- **财务块命名制**——财务内容按类型分块（`table`／`chart_bar`／`timeline`／`text`／`missing`），每块带 `表N｜` 或 `图N｜` 命名行；缺项用 `missing` 显式声明，不静默丢弃。

数据不合契约时，改数据迁就契约——不要改渲染器迁就数据。

**2. 渲染。** `render.py` **先校验后渲染**——结构完整性、来源闭环、导航锚点唯一、命名齐全、图表数据合法性——任何问题都以逐条列出的"校验失败"清单中止，**不出半成品**；通过后填充冻结的 `skeleton.html`，产出完全自包含的页面。

**3. 交付前核验。**

```bash
python renderer/check_urls.py report.json   # 每个来源 URL 可达；标 WARN 的（403/202/429、跨站重定向、超时、TLS 握手中断、网络禁止明文 http）需人工复核——反爬/JS 页面在浏览器里仍可能打开
```

然后在浏览器中打开一次（导航、搜索、MD 导出、图表），确认无**渲染器残留**的 `{{...}}` 令牌——数据值里的字面模板令牌按设计原样保留（渲染器 v0.10+ 单趟替换），不属于缺陷。

## 目录结构

| 路径 | 内容 |
|---|---|
| `SKILL.md` | Skill 入口文件（报告生成段）＋研究段纪律 7 点浓缩清单 |
| `research-discipline-spec.md` | 冻结版（v0.3）研究段纪律与输出格式规范（工具中立） |
| `data-contract/` | `report-data.schema.json` 数据契约 |
| `examples/` | 两个通过校验的数据实例（鸣石／锦浪） |
| `renderer/` | `render.py`、冻结骨架 `skeleton.html`、`compare.py`、`check_urls.py`、测试与模糊闸门；`make_skeleton.py`（仅维护者——公开环境缺内部基线样张会拒绝运行） |
| `samples/` | 成品单文件 HTML 样张（离线可开、可自由分享） |

## 安装

本仓库是标准 agent skill 包（入口：`SKILL.md`）。克隆或复制到您所用 agent 的技能目录即可：

```bash
git clone https://github.com/maleo0228/enterprise-research-skill.git
```

- **Codex**：复制到 `~/.agents/skills/enterprise-research-skill/`（或 `~/.codex/skills/`）
- **Claude Code**：复制到 `~/.claude/skills/enterprise-research-skill/`
- **WorkBuddy**：复制到 `~/.workbuddy/skills/enterprise-research-skill/`（用户级）或 `{workspace}/.workbuddy/skills/enterprise-research-skill/`（项目级）
- **Kimi 及其他 agent**：将技能搜索路径指向本目录；平台不支持自动发现时，直接阅读 `SKILL.md` 并手动执行渲染命令——渲染器是零依赖 CLI（仅需 Python 3.8+ 标准库），独立可用。

安装后重启或刷新 agent 使其重新发现技能。

**范围**：本 skill 覆盖"报告生成段"（合规 JSON → 校验过的 HTML 报告）；产出数据集的研究段由使用者自己的研究工作流完成，行为准则见 [`research-discipline-spec.md`](research-discipline-spec.md)。

## 维护者专用

仅改版渲染器/骨架时：`python renderer/test_renderer.py` 跑 119 项攻击面与回归套件，并必须跑 `python renderer/fuzz_renderer.py` 种子化模糊（4 种子×2000 用例零缺陷）——全部通过才可发版；`python renderer/compare.py <渲染产物.html> <基线样张.html>` 与冻结基线做等价比对。

## 路线图

- **非 IT 行业示例**——v2.3.1 发布后 3 个月内，补充一个制造业或消费类上市公司的完整示例（真实研究后按契约实例化），随后续版本（拟 v2.4.0）发布；进展见更新日志。

## 协议

[MIT](LICENSE)

---

**说明**：本公开仓库发布报告渲染器、数据契约、研究纪律规范（v0.3）与成品样张；方法论文背后的分析框架——模块划分论证、机制分析视角、方向状态机判据、收录阈值与内部案例库——不在公开范围内。
