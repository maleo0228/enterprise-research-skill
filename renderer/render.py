# -*- coding: utf-8 -*-
"""
G5 渲染器 v0.3（无第三方依赖，Python 3.8+ 标准库）
用法: python render.py <report.json> <skeleton.html> <输出.html>
规则依据：《企业研究Skill_G4数据契约与模板规格 v0.1（含增补）》§四/§五
v0.3 变更（2026-10-21，D-75）：
 - Logo 徽章短名超 2 字自适应缩字号（4 字如"词元无限"不再裁切；两字输出与 v0.1/v0.2 逐字节一致）
v0.2 变更（2026-10-21，外部审计 14 项修复，D-72）：
 - rich() 白名单真实落地（b/br/a[href http(s)]，其余标签转义；a 仅放行 https?://）
 - chart_bar 支持负值（含零线；非负数据路径与 v0.1 输出逐字节一致）
 - validate() 增补：meta 必填、块类型枚举、图表 categories 非空/数值/长度一致
 - sources.url/url2 仅 http(s) 生成链接，其余降级为纯文本
 - 结构缺失统一走"校验失败"干净报错，不再裸 traceback
"""
import json, re, sys, html, pathlib

# ---------- 基础工具 ----------
def esc(t):
    return html.escape(str(t), quote=False)

def esc_href(t):  # 与基线一致：& 不转义（浏览器兼容，基线即为 raw &）
    return str(t).replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def sups(sources):
    return "".join(f'<sup class="src" data-e="{e}">[{e}]</sup>' for e in (sources or []))

_TAG_RE = re.compile(r'<(/?)(b|br|a)(?:\s+href="([^"]*)")?\s*(/?)>', re.I)

def rich(t):  # _html 字段白名单：仅 <b> <br> <a href="http(s)://...">，其余标签一律转义
    s = str(t)
    out, last = [], 0
    for m in _TAG_RE.finditer(s):
        seg = s[last:m.start()]
        out.append(seg.replace("<", "&lt;").replace(">", "&gt;"))
        tag = m.group(2).lower()
        if tag == "a":
            if m.group(1):
                out.append("</a>")
            else:
                href = m.group(3) or ""
                out.append(f'<a href="{esc_href(href)}" target="_blank">' if re.match(r"^https?://", href) else "<a>")
        else:
            out.append(f"<{m.group(1) or ''}{tag}>")
        last = m.end()
    out.append(s[last:].replace("<", "&lt;").replace(">", "&gt;"))
    return "".join(out)

def kn_field(v):  # 机制档位：str 或 {text, sources}
    if isinstance(v, dict):
        return esc(v["text"]) + sups(v.get("sources"))
    return esc(v)

STATE_LABEL = {"s1": "优先跟进", "s2": "值得研究", "s3": "持续观察", "s4": "暂缓"}
COLORS = {"blue": "#1a56a0", "orange": "#c2410c", "green": "#4d7c0f", "gray": "#6b7280"}
PAGES = [("p1", "1.0", "企业概览", "1.0企业概览"),
         ("p2", "2.0", "经营事件与信号", "2.0经营事件与信号"),
         ("p3", "3.0", "业务及技术解析", "3.0业务及技术解析"),
         ("p4", "4.0", "IT关注方向及跟进", "4.0IT关注方向及跟进"),
         ("p5", "5.0", "来源索引与证据链", "5.0来源索引与证据链")]

# ---------- 业务校验（不过即失败，不出 HTML） ----------
def validate(d):
    errs = []
    SRC_KEYS = ("sources", "caption_sources", "note_sources", "text_sources")
    refs = []
    def walk(o, loc):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in SRC_KEYS and isinstance(v, list):
                    for e in v:
                        refs.append((loc + "." + k, e))
                else:
                    walk(v, loc + "." + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{loc}[{i}]")
    walk(d, "$")
    declared = [it["id"] for it in d["sources"]["items"]]
    dset = set(declared)
    if len(declared) != len(dset):
        errs.append("来源表存在重复编号")
    for loc, e in refs:
        if not re.match(r"^E\d+$", e) or e not in dset:
            errs.append(f"引用未声明来源 {e} @ {loc}")
    for e in declared:
        if e not in {x for _, x in refs}:
            errs.append(f"来源 {e} 从未被引用")
    navs = [s["id"] for s in d["signals"]["key"]] + [m["id"] for m in d["mechanisms"]["items"]]
    bh = d["overview"]["business"].get("heading")
    if bh and bh.get("id"):
        navs.append(bh["id"])
    if len(navs) != len(set(navs)):
        errs.append("导航 id 重复")
    meta = d.get("meta") or {}
    for k in ("company_name", "company_short", "anchor_date"):
        if not (isinstance(meta.get(k), str) and meta[k].strip()):
            errs.append(f"meta.{k} 缺失或为空")
    BLOCK_TYPES = {"table", "chart_bar", "timeline", "text", "missing"}
    for i, b in enumerate(d["overview"]["financial"]["blocks"]):
        t = b.get("type")
        if t not in BLOCK_TYPES:
            errs.append(f"财务块#{i} 未知块类型：{t!r}（合法：{'/'.join(sorted(BLOCK_TYPES))}）")
            continue
        if t in ("table", "chart_bar", "timeline"):
            cap = b.get("caption", "")
            pat = r"^表\d+｜" if t == "table" else r"^图\d+｜"
            if not re.match(pat, cap):
                errs.append(f"财务块#{i}({t}) 命名行不合规：{cap!r}")
        if t == "chart_bar":
            cats = b.get("categories")
            if not isinstance(cats, list) or not cats:
                errs.append(f"财务块#{i}(chart_bar) categories 缺失或为空")
                cats = []
            for j, sr in enumerate(b.get("series") or []):
                vals = sr.get("values") if isinstance(sr, dict) else None
                if not isinstance(vals, list) or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
                    errs.append(f"财务块#{i} 序列#{j} values 非数值数组")
                elif cats and len(vals) != len(cats):
                    errs.append(f"财务块#{i} 序列#{j} 长度({len(vals)})与 categories({len(cats)})不一致")
    def scan_sup(o, loc):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and ("_html" in k or k in ("text", "note", "timeline_note")) and "<sup" in v:
                    errs.append(f"手写 <sup> @ {loc}.{k}")
                else:
                    scan_sup(v, loc + "." + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan_sup(v, f"{loc}[{i}]")
    scan_sup(d, "$")
    bi = d["overview"]["basic_info"]
    exp = ["公司全称", "官网", "成立时间", "注册地／经营地", "所有制／资本状态", "高管背景", "员工规模", "组织结构"]
    if [x["label"] for x in bi] != exp:
        errs.append("basic_info 字段清单不合规")
    order = ["业务任务", "业务系统", "功能需求", "负载特性", "运行方式", "对业务结果的影响", "关联的 IT 能力"]
    for m in d["mechanisms"]["items"]:
        if [r["th"] for r in m["rows"]] != order:
            errs.append(f"{m['id']} 七行不合规")
    for s in d["signals"]["key"]:
        if [x["label"] for x in s["sections"]] != ["事实依据", "为什么重要", "对关注方向的影响"]:
            errs.append(f"{s['id']} 三段不合规")
    if errs:
        raise SystemExit("校验失败：\n" + "\n".join(" - " + e for e in errs))

# ---------- body 生成 ----------
def render_financial_block(b):
    t = b["type"]
    if t == "table":
        out = [f'  <p style="margin-top:14px"><b>{esc(b["caption"])}</b>{sups(b.get("caption_sources"))}</p>',
               '  <table class="t">',
               "    <tr>" + "".join(f"<th>{esc(h)}</th>" for h in b["header"]) + "</tr>"]
        for r in b["rows"]:
            out.append("    <tr><th>" + esc(r[0]) + "</th>" + "".join(f"<td>{esc(c)}</td>" for c in r[1:]) + "</tr>")
        out.append("  </table>")
        if b.get("note"):
            out.append(f'  <p class="note">{esc(b["note"])}{sups(b.get("note_sources"))}</p>')
        return "\n".join(out)
    if t == "chart_bar":
        n = re.match(r"^图(\d+)｜", b["caption"]).group(1)
        return "\n".join([
            f'  <p style="margin-top:14px"><b>{esc(b["caption"])}</b>{sups(b.get("caption_sources"))}</p>',
            chart_svg(n, b),
            f'  <p class="note">{esc(b.get("chart_note", ""))}</p>'])
    if t == "timeline":
        nodes = []
        for nd in b["nodes"]:
            nodes.append('    <div class="tl-node"><div class="tl-dot"></div><div class="tl-card"><b>'
                         + esc(nd["value"]) + "</b>" + esc(nd["date"])
                         + f'<span class="who">{esc(nd["who"])}</span>{sups(nd["sources"])}</div></div>')
        out = [f'  <p style="margin-top:14px"><b>{esc(b["caption"])}</b>{sups(b.get("caption_sources"))}</p>',
               '  <div class="timeline">', "\n".join(nodes), "  </div>"]
        if b.get("timeline_note"):
            out.append(f'  <p class="note">{rich(b["timeline_note"])}{sups(b.get("note_sources"))}</p>')
        return "\n".join(out)
    if t == "text":
        out = [f'  <p style="margin-top:14px"><b>{esc(b["caption"])}</b>{sups(b.get("caption_sources"))}</p>']
        for blk in b["blocks"]:
            out.append(f'  <p>{rich(blk["text_html"])}{sups(blk["sources"])}</p>')
        return "\n".join(out)
    if t == "missing":
        return f'  <div class="missing">{esc(b["note"])}</div>'
    raise ValueError("未知块类型 " + t)

def chart_svg(n, b):
    cats, series = b["categories"], b["series"]
    base_y, plot_h, x0, gw, bw, bg = 200, 168, 70, 140, 30, 6
    maxv = max(max(s["values"]) for s in series)
    minv = min(min(s["values"]) for s in series)
    names = [s["name"] for s in series]
    aria = f"图{n} {'与'.join(names)}柱状图（{cats[0]}–{cats[-1]}）"
    el = [f'<svg width="660" height="250" viewBox="0 0 660 250" role="img" aria-label="{esc(aria)}" style="margin:6px 0 4px; max-width:100%;">']
    lx = x0
    for s in series:
        c = COLORS[s.get("color", "blue")]
        unit = f'（{s["unit"]}）' if s.get("unit") else ""
        el.append(f'    <rect x="{lx}" y="10" width="10" height="10" fill="{c}" rx="2"/>')
        el.append(f'    <text x="{lx+16}" y="19" font-size="12" fill="#1f2733">{esc(s["name"]+unit)}</text>')
        lx += 150
    if minv >= 0:
        # 非负路径：与 v0.1 输出逐字节一致（基线等价比对依赖）
        ceil = max(10, -(-int(maxv) // 10) * 10)
        k = plot_h / ceil
        for i, _ in enumerate(cats):
            gx = x0 + gw * i
            for j, s in enumerate(series):
                v = s["values"][i]
                h = round(v * k, 1)
                y = round(base_y - h, 1)
                el.append(f'    <rect x="{gx + j*(bw+bg)}" y="{y}" width="{bw}" height="{h}" fill="{COLORS[s.get("color","blue")]}" rx="2"/>')
                el.append(f'    <text x="{gx + j*(bw+bg)}" y="{round(y-6)}" font-size="12" fill="{COLORS[s.get("color","blue")]}">{v:.2f}</text>')
        el.append(f'    <line x1="50" y1="{base_y}" x2="640" y2="{base_y}" stroke="#e3e8ef" stroke-width="1.5"/>')
    else:
        # 负值路径：零线基准双向柱（v0.2 新增，仅数据含负值时启用）
        hi = max(10, -(-int(maxv) // 10) * 10)
        lo = min(-10, (int(minv) // 10) * 10)
        k = plot_h / (hi - lo)
        top_y = 32
        zero_y = round(top_y + hi * k, 1)
        el.append(f'    <line x1="50" y1="{top_y}" x2="640" y2="{top_y}" stroke="#e3e8ef" stroke-width="1"/>')
        for i, _ in enumerate(cats):
            gx = x0 + gw * i
            for j, s in enumerate(series):
                v = s["values"][i]
                c = COLORS[s.get("color", "blue")]
                if v >= 0:
                    h = round(v * k, 1)
                    y = round(zero_y - h, 1)
                    ly = round(y - 6)
                else:
                    h = round(-v * k, 1)
                    y = zero_y
                    ly = round(y + h + 13)
                el.append(f'    <rect x="{gx + j*(bw+bg)}" y="{y}" width="{bw}" height="{h}" fill="{c}" rx="2"/>')
                el.append(f'    <text x="{gx + j*(bw+bg)}" y="{ly}" font-size="12" fill="{c}">{v:.2f}</text>')
        el.append(f'    <line x1="50" y1="{zero_y}" x2="640" y2="{zero_y}" stroke="#1f2733" stroke-width="1.5"/>')
    for i, c in enumerate(cats):
        el.append(f'    <text x="{x0 + gw*i}" y="222" font-size="12.5" fill="#1f2733">{esc(c)}</text>')
    el.append("  </svg>")
    return "\n".join(el)

def render_p1(d):
    o = d["overview"]; b = o["business"]
    L = ['<section class="page" id="p1">',
         '  <div class="page-title"><span class="no">1.0</span><span>企业概览</span></div>',
         f'  <div class="page-lead">{esc(o["lead"])}</div>',
         '  <h3 class="block-title" id="s1-base">基础信息</h3>',
         '  <table class="t kv">']
    for it in o["basic_info"]:
        L.append(f'    <tr><th>{esc(it["label"])}</th><td>{rich(it["value_html"])}{sups(it["sources"])}</td></tr>')
    L.append("  </table>")
    if b.get("heading"):
        h = b["heading"]
        L.append(f'  <h3 class="block-title" id="{h["id"]}">{esc(h["title"])}</h3>')
    if b.get("outline_heading"):
        L.append(f'  <h3 class="block-title">{esc(b["outline_heading"])}</h3>')
    if b.get("outline_title"):
        L.append(f'  <p><b>{esc(b["outline_title"])}</b></p>')
    for it in b["outline_items"]:
        L.append(f'  <p>{("<b>"+esc(it["lead"])+"</b>") if it.get("lead") else ""}{rich(it["text_html"])}{sups(it["sources"])}</p>')
    if b.get("chain_heading"):
        L.append(f'  <h3 class="block-title">{esc(b["chain_heading"])}</h3>')
    for it in b["chain"]:
        if it["label_bold"]:
            L.append(f'  <p><b>{esc(it["label"])}：</b>{rich(it["text_html"])}{sups(it["sources"])}</p>')
        elif it["label"]:
            L.append(f'  <p>{esc(it["label"])}{rich(it["text_html"])}{sups(it["sources"])}</p>')
        else:
            L.append(f'  <p>{rich(it["text_html"])}{sups(it["sources"])}</p>')
    if b.get("strengths_heading"):
        L.append(f'  <h3 class="block-title">{esc(b["strengths_heading"])}</h3>')
    if b.get("strengths_title"):
        L.append(f'  <p><b>{esc(b["strengths_title"])}</b></p>')
    for it in b["strength_items"]:
        L.append(f'  <p>{("<b>"+esc(it["lead"])+"</b>") if it.get("lead") else ""}{rich(it["text_html"])}{sups(it["sources"])}</p>')
    for it in b["moat"]:
        L.append(f'  <p><b>{esc(it["label"])}</b>{rich(it["text_html"])}{sups(it["sources"])}</p>')
    L += ['  <h3 class="block-title" id="s1-fin">财务数据</h3>',
          f'  <p class="note">{esc(o["financial"]["lead_note"])}</p>']
    for blk in o["financial"]["blocks"]:
        L.append(render_financial_block(blk))
    L.append('  <div class="export-row"><button class="export-btn" data-sec="p1" data-name="1.0企业概览" title="导出为 Markdown 文件">导出 MD</button></div>')
    L.append("</section>")
    return "\n".join(L)

def render_p2(d):
    s = d["signals"]
    L = ['<section class="page" id="p2">',
         '  <div class="page-title"><span class="no">2.0</span><span>经营事件与信号</span></div>',
         f'  <div class="page-lead">{esc(s["lead"])}</div>']
    for sig in s["key"]:
        L.append(f'  <div class="signal" id="{sig["id"]}">')
        L.append(f'    <h4>{esc(sig["title"])}</h4>')
        for sec in sig["sections"]:
            L.append(f'    <p><span class="lbl">{esc(sec["label"])}：</span>{rich(sec["text_html"])}{sups(sec["sources"])}</p>')
        L.append("  </div>")
    dyn_id = ' id="sig-dyn"' if s.get("dynamic_nav") else ""
    L.append(f'  <h3 class="block-title"{dyn_id}>{esc(s["dynamic_title"])}</h3>')
    L.append('  <ul class="dyn-list">')
    for it in s["dynamic"]:
        L.append(f'    <li><b>{esc(it["id"])}</b>｜{rich(it["text_html"])}{sups(it["sources"])}</li>')
    L.append("  </ul>")
    L.append('  <div class="export-row"><button class="export-btn" data-sec="p2" data-name="2.0经营事件与信号" title="导出为 Markdown 文件">导出 MD</button></div>')
    L.append("</section>")
    return "\n".join(L)

def render_p3(d):
    L = ['<section class="page" id="p3">',
         '  <div class="page-title"><span class="no">3.0</span><span>业务及技术解析</span></div>',
         f'  <div class="page-lead">{esc(d["mechanisms"]["lead"])}</div>']
    for m in d["mechanisms"]["items"]:
        L.append(f'  <div class="mech" id="{m["id"]}">')
        L.append(f'    <h4>{esc(m["title"])}</h4>')
        L.append('    <table class="t">')
        for r in m["rows"]:
            L.append(f'      <tr><th>{esc(r["th"])}</th><td>{rich(r["td_html"])}{sups(r["sources"])}</td></tr>')
        L.append("    </table>")
        L.append(f'    <p class="kn"><span class="k1">已确认：</span>{kn_field(m["confirmed"])}</p>')
        L.append(f'    <p class="kn"><span class="k2">未确认：</span>{kn_field(m["unconfirmed"])}</p>')
        L.append(f'    <p class="evi">{kn_field(m["evidence"])}</p>')
        L.append("  </div>")
    L.append('  <div class="export-row"><button class="export-btn" data-sec="p3" data-name="3.0业务及技术解析" title="导出为 Markdown 文件">导出 MD</button></div>')
    L.append("</section>")
    return "\n".join(L)

def render_p4(d):
    L = ['<section class="page" id="p4">',
         '  <div class="page-title"><span class="no">4.0</span><span>IT关注方向及跟进</span></div>',
         f'  <div class="page-lead">{esc(d["directions"]["lead"])}</div>']
    for it in d["directions"]["items"]:
        L.append('  <div class="dir">')
        L.append(f'    <div class="dir-head"><span class="tag {it["state"]}">{STATE_LABEL[it["state"]]}</span><h4>{esc(it["title"])}</h4></div>')
        L.append(f'    <div class="basis">{esc(it["basis"])}</div>')
        for p in it["points"]:
            L.append(f'    <p><span class="lbl">{esc(p["label"])}：</span>{rich(p["text_html"])}</p>')
        L.append("  </div>")
    L.append('  <div class="export-row"><button class="export-btn" data-sec="p4" data-name="4.0IT关注方向及跟进" title="导出为 Markdown 文件">导出 MD</button></div>')
    L.append("</section>")
    return "\n".join(L)

def render_p5(d):
    s = d["sources"]
    L = ['<section class="page" id="p5">',
         '  <div class="page-title"><span class="no">5.0</span><span>来源索引与证据链</span></div>',
         f'  <div class="page-lead">{esc(s["lead"])}</div>',
         '  <h3 class="block-title">身份怎么读</h3>',
         '  <div class="legend">']
    for x in s.get("legend", []):
        L.append(f'    <span>{esc(x)}</span>')
    L += ["  </div>",
          '  <h3 class="block-title">来源记录（点击正文 [E#] 可跳到此表对应行）</h3>',
          '  <table class="t" id="src-table">',
          "    <tr><th>编号</th><th>主体</th><th>时间</th><th>口径</th><th>来源与层级</th><th>链接</th><th>获取日期</th><th>身份</th></tr>"]
    def src_link(url, display, title=""):
        if url and re.match(r"^https?://", url):
            return f'<a href="{esc_href(url)}" target="_blank"{title}>{esc(display)}</a>'
        return esc(display)
    for it in s["items"]:
        title = ' title="该来源链接在研究记录中不完整，溯源至网站首页"' \
            if ("…" in it["url_display"] and re.match(r"^https?://[^/?#]+/?$", it["url"])) else ""
        href = src_link(it["url"], it["url_display"], title)
        if it.get("url2"):
            href += src_link(it["url2"], it["url2_display"])
        L.append(f'    <tr id="{it["id"]}"><td class="eid">{it["id"]}</td><td>{esc(it["entity"])}</td>'
                 f'<td>{esc(it["time"])}</td><td>{esc(it["caliber"])}</td><td>{esc(it["source"])}</td>'
                 f'<td class="url">{href}</td>'
                 f'<td>{esc(it["fetched"])}</td><td>{esc(it["identity"])}</td></tr>')
    L += ["  </table>",
          '  <h3 class="block-title">同源关系说明</h3>',
          f'  <p class="note">{esc(s["homology_note"])}</p>',
          '  <div class="export-row"><button class="export-btn" data-sec="p5" data-name="5.0来源索引与证据链" title="导出为 Markdown 文件">导出 MD</button></div>',
          "</section>"]
    return "\n".join(L)

def render_sidenav(d):
    o, s, m = d["overview"], d["signals"], d["mechanisms"]
    L = ['    <a class="grp" href="#p1" data-t="企业概览">企业概览</a>',
         '    <a class="sub" href="#s1-base" data-t="基础信息">基础信息</a>']
    bh = o["business"].get("heading")
    if bh and bh.get("nav"):
        L.append(f'    <a class="sub" href="#{bh["id"]}" data-t="{esc(bh["nav"])}">{esc(bh["nav"])}</a>')
    L.append('    <a class="sub" href="#s1-fin" data-t="财务数据">财务数据</a>')
    L.append('    <a class="grp" href="#p2" data-t="经营事件与信号">经营事件与信号</a>')
    for sig in s["key"]:
        L.append(f'    <a class="sub" href="#{sig["id"]}" data-t="{esc(sig["nav"])}">{esc(sig["nav"])}</a>')
    if s.get("dynamic_nav"):
        L.append(f'    <a class="sub" href="#sig-dyn" data-t="{esc(s["dynamic_nav"])}">{esc(s["dynamic_nav"])}</a>')
    L.append('    <a class="grp" href="#p3" data-t="业务及技术解析">业务及技术解析</a>')
    for mech in m["items"]:
        L.append(f'    <a class="sub" href="#{mech["id"]}" data-t="{esc(mech["nav"])}">{esc(mech["nav"])}</a>')
    L.append('    <a class="grp" href="#p4" data-t="IT关注方向及跟进">IT关注方向及跟进</a>')
    L.append('    <a class="grp" href="#p5" data-t="来源索引与证据链">来源索引与证据链</a>')
    return "\n".join(L)

# ---------- 主流程 ----------
def main():
    data_p, skel_p, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
    d = json.load(open(data_p, encoding="utf-8"))
    validate(d)
    meta = d["meta"]
    skel = pathlib.Path(skel_p).read_text(encoding="utf-8")
    body = "\n\n".join([render_p1(d), render_p2(d), render_p3(d), render_p4(d), render_p5(d)])
    # Logo 徽章：短名超 2 字时按行数自适应缩字号（两字输出与历史基线逐字节一致）
    short = meta["company_short"]
    lines = -(-len(short) // 2)  # 每行最多 2 字
    fs = min(20, max(9, int(40 // (1.15 * lines))))
    badge = (f'<div class="logo-badge" style="font-size:{fs}px; line-height:1.15;">{esc(short)}</div>'
             if fs < 20 else f'<div class="logo-badge">{esc(short)}</div>')
    out = (skel.replace("{{COMPANY_NAME}}", meta["company_name"])
              .replace("{{SAMPLE_VERSION}}", meta.get("sample_version", ""))
              .replace('<div class="logo-badge">{{SHORT}}</div>', badge)
              .replace("{{ANCHOR_DATE}}", meta["anchor_date"])
              .replace("{{SEARCH_HINT}}", meta.get("search_hint", "输入关键词……"))
              .replace("{{SIDENAV}}", render_sidenav(d))
              .replace("{{BODY}}", body))
    pathlib.Path(out_p).write_text(out, encoding="utf-8")
    print(f"渲染完成：{out_p}（{len(out.encode('utf-8'))} 字节）")

if __name__ == "__main__":
    main()
