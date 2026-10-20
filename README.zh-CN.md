# Enterprise Research Skill｜企业深度研究 Skill

**基于公开证据的企业研究 → 单文件交互式 HTML 报告。**
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

```
研究底稿 → report.json（按数据契约填写）→ render.py → 成品 HTML
```

1. 按数据契约（[`data-contract/report-data.schema.json`](data-contract/report-data.schema.json)）填写 `report.json`，[`examples/`](examples/) 内有两个通过校验的实例（鸣石／锦浪）；
2. 渲染——一条命令，**零第三方依赖**（仅需 Python 3.8+ 标准库）：

   ```bash
   python renderer/render.py report.json renderer/skeleton.html report.html
   ```

   渲染器先执行业务校验（来源闭环、导航唯一、命名齐全、禁手写引用标），**校验不过直接失败，不出半成品**；
3. 改版回归用 `renderer/compare.py` 与基线样张做等价比对。

## 目录结构

| 路径 | 内容 |
|---|---|
| `samples/` | 成品单文件 HTML 样张（离线可开、可自由分享） |
| `renderer/` | `render.py`、`skeleton.html`（冻结页面骨架）、`compare.py`、`make_skeleton.py` |
| `data-contract/` | `report-data.schema.json` 数据契约 |
| `examples/` | 两个通过校验的数据实例（鸣石／锦浪） |

## 协议

[MIT](LICENSE)

---

**说明**：本公开仓库只发布报告渲染器、数据契约与成品样张；支撑方法论的研究规则文件不在公开范围内。
