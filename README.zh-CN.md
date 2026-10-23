# Enterprise Research Skill｜企业深度研究 Skill

**基于公开证据的企业研究 → 单文件交互式 HTML 报告。**
**当前版本：v2.0.13** ·[更新日志](https://github.com/maleo0228/enterprise-research-skill/releases)
v2.0 是对 v1.x 的**完全重写**（v1.x 产出 Markdown＋CSV＋Excel，已归档，见 [Releases](https://github.com/maleo0228/enterprise-research-skill/releases)）。

## 它做什么

对指定企业开展基于公开信息的研究，产出**单文件、可离线打开、可直接分享**的 HTML 报告，包含五个模块：

- **1.0 企业概览**——基础信息、股权与融资、完整财务数据与图表；
- **2.0 经营事件与信号**——有来源的经营事件与分级信号；
- **3.0 业务及技术解析**——按机制逐条拆解，"已确认／未确认"显式分离；
- **4.0 IT 关注方向及跟进**——按证据强度分级的 IT 方向与跟进建议；
- **5.0 来源索引与证据链**——每个关键结论可回溯到编号来源（含原始链接）。

报告支持页面内导航、全文搜索、按模块或全文导出 Markdown。

## 样张（可直接打开，无需服务器）

- **锦浪科技（Ginlong/Solis）**——[ginlong-solis_2026-10-19.html](https://maleo0228.github.io/enterprise-research-skill/samples/ginlong-solis_2026-10-19.html)

## 工作原理

本仓库只覆盖**报告生成段**：研究由你的工作流完成，渲染器负责把数据集变成报告。三步：

```
你的研究  →  report.json（按数据契约填写）  →  render.py  →  成品 HTML
```

**1. 准备数据集。** 把研究结论结构化为一个符合 [`data-contract/report-data.schema.json`](data-contract/report-data.schema.json) 的 `report.json`。[`examples/`](examples/) 内有两个通过校验的实例（鸣石／锦浪）展示完整形态：五个模块、编号来源表、逐条结论的 `sources` 数组。契约硬性规则：

- **来源闭环**——每条结论以 `[E#]` 引用，每个 `[E#]` 在来源表声明，每个声明的来源都被实际引用；环环相扣，无孤证。
- **引用标记由渲染器生成，禁止手写**——数据只提供 `sources` 数组，渲染器自动输出 `[E#]`；手写引用标记会被拒绝。
- **财务块命名制**——财务内容按类型分块（`table`／`chart_bar`／`timeline`／`text`／`missing`），每块带 `表N｜` 或 `图N｜` 命名行；缺项用 `missing` 显式声明，不静默丢弃。

数据不合契约时，改数据迁就契约——不要改渲染器迁就数据。

**2. 渲染。** 一条命令，**零第三方依赖**（仅需 Python 3.8+ 标准库，无网络、无构建步骤）：

```bash
python renderer/render.py report.json renderer/skeleton.html report.html
```

`render.py` **先校验后渲染**——结构完整性、来源闭环、导航锚点唯一、命名齐全、图表数据合法性——任何问题都以逐条列出的"校验失败"清单中止，**不出半成品**。通过后填充冻结的 `skeleton.html`，产出完全自包含的页面：侧边导航、全文搜索、SVG 图表（支持负值）、可点击跳转来源表的 `[E#]` 锚点、按模块与全文导出 Markdown。

**3. 交付前核验。**

```bash
python renderer/check_urls.py report.json   # 每个来源 URL 可达；被标 403/202 的需人工复核
```

然后在浏览器中打开一次（导航、搜索、MD 导出、图表），确认无 `{{...}}` 令牌残留。

**维护者专用**（仅改版渲染器/骨架时）：`python renderer/test_renderer.py` 跑 100 项攻击面与回归套件（另可跑 `python renderer/fuzz_renderer.py` 做种子化模糊测试）——发版前必须全绿；`python renderer/compare.py <渲染产物.html> <基线样张.html>` 与冻结基线做等价比对。

## 目录结构

| 路径 | 内容 |
|---|---|
| `SKILL.md` | Skill 入口文件（报告生成段） |
| `samples/` | 成品单文件 HTML 样张（离线可开、可自由分享） |
| `renderer/` | `render.py`、`skeleton.html`（冻结页面骨架）、`compare.py`、`make_skeleton.py` |
| `data-contract/` | `report-data.schema.json` 数据契约 |
| `examples/` | 两个通过校验的数据实例（鸣石／锦浪） |

## 安装

本仓库是标准 agent skill 包（入口：`SKILL.md`）。克隆或复制到您所用 agent 的技能目录即可：

```bash
git clone https://github.com/maleo0228/enterprise-research-skill.git
```

- **Codex**：复制到 `~/.agents/skills/enterprise-research-skill/`（或 `~/.codex/skills/`）
- **Claude Code**：复制到 `~/.claude/skills/enterprise-research-skill/`
- **WorkBuddy / CodeBuddy**：复制到项目内 `.codebuddy/skills/enterprise-research-skill/`（或用图形化技能管理页导入）
- **Kimi 及其他 agent**：将技能搜索路径指向本目录；平台不支持自动发现时，直接阅读 `SKILL.md` 并手动执行渲染命令——渲染器是零依赖 CLI（仅需 Python 3.8+ 标准库），独立可用。

安装后重启或刷新 agent 使其重新发现技能。

**范围说明**：本 skill 覆盖"报告生成段"（合规 JSON → 校验过的 HTML 报告）；产出数据集的研究段由使用者自己的研究工作流完成。

## 协议

[MIT](LICENSE)

---

**说明**：本公开仓库只发布报告渲染器、数据契约与成品样张；支撑方法论的研究规则文件不在公开范围内。
