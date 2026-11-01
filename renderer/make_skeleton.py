# -*- coding: utf-8 -*-
"""从鸣石 v0.8 提取冻结骨架，替换公司特定内容为令牌，生成 skeleton.html
注意：本脚本依赖工作区私有基线样张（鸣石 v0.8），公开仓库环境不可运行——
skeleton.html 是冻结产物；版式变更须在持有基线的工作区内执行本流程。"""
import re, pathlib

_SRC = pathlib.Path("企业研究Skill_G3样张_上海鸣石销售成品_v0.8.html")
if not _SRC.exists():
    raise SystemExit(
        "缺少基线样张：企业研究Skill_G3样张_上海鸣石销售成品_v0.8.html（工作区私有文件，公开仓库不提供）。\n"
        "skeleton.html 为冻结产物，请勿在公开环境再生骨架；版式变更请在持有基线的工作区内执行本脚本。")
src = _SRC.read_text(encoding="utf-8")

s = src
s = s.replace("<title>企业研究报告：上海鸣石私募基金管理有限公司（销售成品样张 v0.8）</title>",
              "<title>企业研究报告：{{COMPANY_NAME}}（销售成品样张 {{SAMPLE_VERSION}}）</title>")
s = s.replace('placeholder="输入关键词，如：超算、备案、风控……"', 'placeholder="{{SEARCH_HINT}}"')
s = s.replace('<div class="logo-badge">鸣石</div>', '<div class="logo-badge">{{SHORT}}</div>')
s = s.replace('<div class="logo-name">上海鸣石私募基金管理有限公司</div>', '<div class="logo-name">{{COMPANY_NAME}}</div>')
s = s.replace('<div class="logo-sub">企业研究报告 · 锚点 2026-10-14</div>', '<div class="logo-sub">企业研究报告 · 锚点 {{ANCHOR_DATE}}</div>')
s = re.sub(r'(<nav class="sidenav" id="sidenav">).*?(</nav>)', r'\1\n{{SIDENAV}}\n  \2', s, flags=re.S)
s = re.sub(r'(<div class="content" id="content">).*?(</div>\r?\n\r?\n<footer>)', r'\1\n{{BODY}}\n\2', s, flags=re.S)
s = s.replace("<footer>本报告基于公开信息整理，锚点日期 2026-10-14。</footer>", "<footer>本报告基于公开信息整理，锚点日期 {{ANCHOR_DATE}}。</footer>")
s = s.replace('var out="# 企业研究报告：上海鸣石私募基金管理有限公司\\n\\n> 锚点日期 2026-10-14；本报告基于公开信息整理。',
              'var out="# 企业研究报告：{{COMPANY_NAME}}\\n\\n> 锚点日期 {{ANCHOR_DATE}}；本报告基于公开信息整理。')
s = s.replace('企业研究_鸣石_', '企业研究_{{SHORT}}_')

# v2.3.4：全文导出按钮由 position:fixed 浮层移入边栏标题区（R18）——基线 v0.8 仍是浮层写法，在此改写，
# 保证在持有基线的工作区重新冻结时不会把浮层带回来。三处替换必须各命中一次。
_EXP = [
    ("  .export-fixed{position:fixed; top:14px; right:16px; z-index:60;}\n",
     "  /* 全文导出按钮放进边栏标题区（不再 position:fixed 浮在正文上）：桌面随固定边栏常驻可见，\n"
     "     ≤920px 边栏变为页首静态块，按钮随之成为页首行内元素——任何宽度都不压正文 */\n"
     "  .export-side{display:inline-block; margin-top:8px;}\n"),
    ('<button id="export-all" class="export-btn export-fixed" title="导出全篇为 Markdown 文件">导出全文 MD</button>\n\n', ""),
    ('      <div class="logo-sub">企业研究报告 · 锚点 {{ANCHOR_DATE}}</div>\n',
     '      <div class="logo-sub">企业研究报告 · 锚点 {{ANCHOR_DATE}}</div>\n'
     '      <button id="export-all" class="export-btn export-side" title="导出全篇为 Markdown 文件">导出全文 MD</button>\n'),
]
for _a, _b in _EXP:
    assert s.count(_a) == 1, "基线导出按钮写法与预期不符：" + _a[:40]
    s = s.replace(_a, _b)

# v2.3.5（评审补丁 v6）：0003 加宽图桌面 11px、0004 图内搜索用 <tspan>、0005 单栏导航精简——同样以改写方式
# 落到基线上，保证在持有基线的工作区重新冻结时与 skeleton.html 逐字节一致。每处替换必须各命中一次。
_V6 = [
    ('  .chart-scroll{overflow-x:auto; -webkit-overflow-scrolling:touch;}\n',
     '  .chart-scroll{overflow-x:auto; -webkit-overflow-scrolling:touch;}\n  .chart-scroll>svg{min-width:var(--chart-minw-wide,0);} /* 加宽画布的图：桌面也保底 11px */\n'),
    ('  mark.hit.cur{background:#ffb900;}\n',
     '  mark.hit.cur{background:#ffb900;}\n  /* 图内（SVG）命中：HTML <mark> 在 <text> 里不渲染、会把文字吞掉，改用 SVG <tspan> 着色 */\n  tspan.hit{fill:#b45309; text-decoration:underline;}\n  tspan.hit.cur{fill:#c2410c; font-weight:700;}\n'),
    ('  .export-side{display:inline-block; margin-top:8px;}\n',
     '  .export-side{display:inline-block; margin-top:8px;}\n  /* 单栏版式导航精简（可选）：侧栏在手机上原本占满首屏（≈710px），子项隐藏、五个一级入口排成一行可换行的标签 */\n  @media(max-width:920px){\n    .sidenav{display:flex; flex-wrap:wrap; gap:6px; padding:4px 16px 14px;}\n    .sidenav .sub{display:none;}\n    .sidenav .grp{padding:3px 10px; border:1px solid var(--line); font-size:13px;}\n  }\n'),
    ('  function clearHits(){\n    content.querySelectorAll("mark.hit").forEach(function(m){\n',
     '  function clearHits(){\n    content.querySelectorAll("mark.hit, tspan.hit").forEach(function(m){\n'),
    ('        if(!n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;\n        if(n.parentElement.closest("script,style,mark")) return NodeFilter.FILTER_REJECT;\n',
     '        if(!n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;\n        if(n.parentElement.closest("script,style,mark,tspan.hit")) return NodeFilter.FILTER_REJECT;\n'),
    ('    nodes.forEach(function(n){\n      var el=n.parentNode, txt=n.nodeValue, ltxt=txt.toLowerCase();\n',
     '    nodes.forEach(function(n){\n      var el=n.parentNode, txt=n.nodeValue, ltxt=txt.toLowerCase(),\n          inSvg=(el.namespaceURI==="http://www.w3.org/2000/svg");\n'),
    ('        frag.appendChild(document.createTextNode(txt.slice(idx, pos)));\n        var m=document.createElement("mark");\n        m.className="hit"; m.textContent=txt.slice(pos, pos+k.length);\n',
     '        frag.appendChild(document.createTextNode(txt.slice(idx, pos)));\n        var m=inSvg?document.createElementNS("http://www.w3.org/2000/svg","tspan"):document.createElement("mark");\n        m.setAttribute("class","hit"); m.textContent=txt.slice(pos, pos+k.length);\n'),
    ('  function svgToMd(ch){\n    return "> 📊 "+(ch.getAttribute("aria-label")||"图表")+"（图形见网页版）\\n\\n"+(ch.getAttribute("data-md")?ch.getAttribute("data-md")+"\\n\\n":"");\n',
     '  function svgToMd(ch){\n    return "> 📊 "+(ch.getAttribute("aria-label")||"图表").replace(/\\s+/g," ")+"（图形见网页版）\\n\\n"+(ch.getAttribute("data-md")?ch.getAttribute("data-md")+"\\n\\n":"");\n'),
]
for _a, _b in _V6:
    assert s.count(_a) == 1, "基线写法与预期不符：" + _a[:40]
    s = s.replace(_a, _b)

leftovers = [x for x in ["鸣石", "2026-10-14", "超算、备案"] if x in s]
tokens = ["{{COMPANY_NAME}}", "{{SAMPLE_VERSION}}", "{{SEARCH_HINT}}", "{{SHORT}}",
          "{{ANCHOR_DATE}}", "{{SIDENAV}}", "{{BODY}}"]
missing = [t for t in tokens if t not in s]

out = pathlib.Path("_build/g5")
out.mkdir(parents=True, exist_ok=True)
(out / "skeleton.html").write_text(s, encoding="utf-8")
print("骨架已生成：_build/g5/skeleton.html（%d 字节）" % len(s.encode("utf-8")))
print("残留公司特定内容:", leftovers or "无")
print("缺失令牌:", missing or "无")
assert not leftovers and not missing
