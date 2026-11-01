# -*- coding: utf-8 -*-
"""
G5 渲染器 v0.11（无第三方依赖，Python 3.8+ 标准库）
用法: python render.py <report.json> <skeleton.html> <输出.html>
规则依据：《企业研究Skill_G4数据契约与模板规格 v0.1（含增补）》§四/§五
v0.11 变更（2026-10-23，第四轮外部审计 G 系列，验证为真修复，D-95）：
- G8：business.heading 置换为真值非对象时渲染期 AttributeError 裸崩（审计方
  fuzz 种子 777/31337 共 4 用例同源此路径）——校验期拦截：heading 须为对象、
  id/title 必填（渲染期直接索引）、nav 可选须字符串；套件 3 例类型置换回归
- G3：precise 锚点（JS 串/徽章）对骨架文案隐式耦合——锚点失配时此前静默退化
  为 HTML 语境替换，JS 串 esc_js 失效（短名含引号可未转义直通）。改 fail-fast：
  锚点缺失＝骨架/渲染器版本 skew，干净报错不出半成品（冻结产物须同源交付）
- G1：sentinel 保留序列（_SENT 提升为模块级常量）与数据值域隔离——meta 三字段
  含保留序列干净拒绝，防徽章污染/精确替换错位（自伤型输入纵深防御）
- 附带修复 _dbg_md_test.js：argv 差一（读脚本自身不读骨架）＋提取正则未随
  inline(el, depth) 签名更新（第三轮 F10 判定的遗留低危项）
- 对 v0.10 及以前全部合法输入输出逐字节兼容（三样张等价比对回归锁定，套件 95→99 项）
v0.10 变更（2026-10-23，红队 M4 收尾，D-94）：
- 令牌单次扫描替换（红队 A8）：原逐次 str.replace 链中，先插入产物里的 meta 值
  会被后续 replace 二次扫描——company_name 含 {{SHORT}}、短名含 {{BODY}} 等
  "数据撞令牌"会被交叉替换、数据遭篡改。改为 re.sub 单次扫描＋sentinel 保护
  精确语境目标（JS 串/徽章），插入值一律不参与扫描，数据令牌字面量原样留产物；
  基线数据不含令牌，输出与 v0.9 逐字节一致（三样张等价比对锁定，套件 84→95 项）
- 骨架导出 JS 畸形 DOM 桩纵深防御（红队 A9，配套 node stub 测试）：inline 深度
  护栏 40（循环引用）、childNodes/children/querySelectorAll 缺省兜底、
  SVGAnimatedString 类 className、导出按钮 try/catch 不抛裸错；
  真实 DOM 路径输出与 v0.9 逐字一致
- 等价比对盲区登记（红队 A10）：compare.py 文档化六类盲区及逐项处置，
  其中锚点闭环/[E#] 行闭环/导出按钮 data-name 三项并入套件独立断言
v0.9 变更（2026-10-22，红队 M3 fuzz_renderer.py 驱动，8000 用例 4 种子，D-93）：
- 容器字段置换全面兜底：validate 逐项循环统一走 lst()（仅确认为数组才迭代），
  数值/布尔置换的容器字段不再裸崩 TypeError（fuzz 发现：dynamic/key/items/outline_items）
- 财务块 type 非字符串显式报错（原 unhashable 裸崩）；业务校验段同款加固
- 引用源编号非字符串（嵌套数组/对象置换）干净拒绝（原 re.match 裸崩）；
  引用源字段（sources/caption_sources 等）被置换成非数组/对象时显式报错（原静默漏检），
  根节点 sources 节容器除外（对象合法，按路径豁免）
- 来源表/导航 id 非字符串显式报错（原 set() 裸崩）；
  导航 id 字符集收窄为 ^[A-Za-z0-9_-]+$（属性位/锚点防脏污）
- directions.state 枚举校验（渲染期 STATE_LABEL KeyError 裸崩；数组/对象置换使
  校验 in 判重自身 unhashable，先判 str）
- sources 记录全字段字符串校验（url re.match / url_display 子串判断裸崩）；
  url2 与 url2_display 成对校验（KeyError 裸崩）；legend 数组校验
- 财务块结构校验补全：caption 非字符串（re.match 裸崩）、table 行须非空数组（r[0]
  下标裸崩）、chart_bar series/categories 须数组且序列元素须对象（迭代/下标裸崩）、
  series name/unit 字符串与 color 枚举（拼接裸崩 / COLORS KeyError，color 先判 str）、
  timeline nodes 与 text blocks 数组校验
- note_sources 宿主一致性（P3 产物层引用闭环）：table 须有 note、timeline 须有
  timeline_note、chart_bar/text/missing 不支持 note_sources——校验计为已引用而渲染
  不输出的字段一律拒绝（fuzz 发现：删 note 后 E19/E20 产物层断链）
- basic_info label 非字符串显式报错（set 判重 unhashable）
- sups()/kn_field() 纵深防御：非数组 sources 静默返回空（进程内直调 render 函数时
  绕过 main 校验的最后一道兜底）
- 对 v0.8 及以前全部合法输入输出逐字节兼容（双样张等价比对回归锁定）
v0.8 变更（2026-10-22，红队 M2 修复，D-91）：
- 结构容器类型校验（need_list：sections/rows/points 等容器字段非数组显式报错，红队 A6）
- meta 根类型校验（非对象干净拒绝）
- 图表数值有限性校验（NaN/Inf 干净拒绝，红队 A7）
- 对 v0.7 及以前全部合法输入输出逐字节兼容（双样张等价比对回归锁定）
v0.7 变更（2026-10-22，红队 M1 修复，D-88）：
- meta 令牌按语境转义（红队 A4 发现：company_name/anchor_date/search_hint 等
  原先无转义直通 HTML 文本/属性/JS 字符串三种语境）：
  JS 串语境（下载文件名/MD 导出头）用 esc_js 转义（防 </script> 突破与串内注入），
  HTML 属性语境 esc_attr，HTML 文本语境 esc
- URL scheme 大小写兼容（HTTPS:// 不再降级为纯文本；红队 A5）
- 对 v0.6 及以前全部合法输入输出逐字节兼容（双样张等价比对回归锁定）
v0.6 变更（2026-10-22，第三轮审计 6 项修复 F13/F1/F2/F3/F8，D-86，契约/测试/代码同源交付）：
- validate() 新增结构完整性自查（schema 无人执行，渲染器兜底）：渲染所需全部必填路径
  缺失时统一"校验失败"干净报错，不再裸 traceback（F3，七类场景回归锁定）
- esc_attr() 属性位转义双引号：aria-label/data-t/id/href 等属性插值防突破（F2）
- rich() 白名单 a 标签兼容单引号 href，输出统一双引号（F8）
- 命名行/扩展项校验口径与 schema v0.3 对齐（table 强制 表N｜；basic_info 核心 8 项后放行扩展）
- 对 v0.5 及以前全部合法输入输出逐字节兼容（双样张等价比对回归锁定）
v0.5 变更（2026-10-22，{{SHORT}} 全局兜净修复＋令牌残留测试，D-82/D-83）：
- v0.4 变更（2026-10-21，外部审计二次实测 N1/N2/N8 修复，D-76）：
 - directions 支持挂来源：basis_sources 与 points[].sources 渲染 [E#] 标记
 - basic_info 允许 8 项核心之后追加尽调扩展项（注册资本/信用代码等）
 - signals.dynamic 支持可选 date 字段（日期不再塞进 id）
v0.3 变更（2026-10-21，D-75）：
 - Logo 徽章短名超 2 字自适应缩字号（4 字如"词元无限"不再裁切；两字输出与 v0.1/v0.2 逐字节一致）
v0.2 变更（2026-10-21，外部审计 14 项修复，D-72）：
 - rich() 白名单真实落地（b/br/a[href http(s)]，其余标签转义；a 仅放行 https?://）
 - chart_bar 支持负值（含零线；非负数据路径与 v0.1 输出逐字节一致）
 - validate() 增补：meta 必填、块类型枚举、图表 categories 非空/数值/长度一致
 - sources.url/url2 仅 http(s) 生成链接，其余降级为纯文本
 - 结构缺失统一走"校验失败"干净报错，不再裸 traceback
"""
import json, re, sys, html, pathlib, math

# ---------- 基础工具 ----------
def esc(t):
    return html.escape(str(t), quote=False)

def esc_attr(t):  # 属性位转义：双引号一并转义（F2：aria-label/data-t 等属性注入防护）
    return html.escape(str(t), quote=True)

def esc_js(t):  # JS 字符串字面量转义（红队 A4：下载文件名/MD 导出头，防串内注入与 </script> 突破）
    return (str(t).replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", "\\n").replace("\r", "\\r")
            .replace("<", "\\u003c").replace(">", "\\u003e"))

def esc_href(t):  # 与基线一致：& 不转义（浏览器兼容，基线即为 raw &）
    return str(t).replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# 令牌替换 sentinel（v0.11 提升为模块级常量）：validate 与 main 共用，
# 数据侧拒绝含该保留序列的输入（第四轮审计 G1），替换侧检测骨架锚点失配（G3）
_SENT = "\x00G5TOK%d\x00"

def sups(sources):
    # 红队 M3 fuzz 纵深防御：validate 已保证合法输入为字符串数组；
    # 进程内直调 render 函数（绕过 main 校验）时不让非数组裸崩
    if not isinstance(sources, list):
        return ""
    return "".join(f'<sup class="src" data-e="{e}">[{e}]</sup>' for e in sources)

# 纯文本引用标记：[E9]、［E9］、（E9）、(E9, E10)、（E9／E10）
_PLAIN_CITE_RE = re.compile(r"[\[［（(]\s*E\d+(?:\s*[、,，/／;；]\s*E\d+)*\s*[\]］）)]")

_TAG_RE = re.compile(r'<(/?)(b|br|a)(?:\s+href\s*=\s*(?:"([^"]*)"|\'([^\']*)\'))?\s*(/?)>', re.I)

def rich(t):  # _html 字段白名单：仅 <b> <br> <a href="http(s)://...">（单引号 href 亦认，F8），其余标签一律转义
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
                href = m.group(3) if m.group(3) is not None else (m.group(4) or "")
                out.append(f'<a href="{esc_href(href)}" target="_blank">' if re.match(r"^https?://", href, re.I) else "<a>")
        else:
            out.append(f"<{m.group(1) or ''}{tag}>")
        last = m.end()
    out.append(s[last:].replace("<", "&lt;").replace(">", "&gt;"))
    return "".join(out)

def kn_field(v):  # 机制档位：str 或 {text, sources}
    if isinstance(v, dict):
        return esc(v.get("text", "")) + sups(v.get("sources"))
    return esc(v)

STATE_LABEL = {"s1": "优先跟进", "s2": "值得研究", "s3": "持续观察", "s4": "暂缓"}
COLORS = {"blue": "#1a56a0", "orange": "#c2410c", "green": "#4d7c0f", "gray": "#6b7280"}
PAGES = [("p1", "1.0", "企业概览", "1.0企业概览"),
         ("p2", "2.0", "经营事件与信号", "2.0经营事件与信号"),
         ("p3", "3.0", "业务及技术解析", "3.0业务及技术解析"),
         ("p4", "4.0", "IT关注方向及跟进", "4.0IT关注方向及跟进"),
         ("p5", "5.0", "来源索引与证据链", "5.0来源索引与证据链")]

# ---------- 业务校验（不过即失败，不出 HTML） ----------
WARNS = []  # 非阻断的契约警告（--strict 时升级为校验失败）

def validate(d, strict=False):
    errs = []
    warns = []

    # ---- 结构完整性自查（F3，2026-10-22 第三轮审计）----
    # schema 无人执行，渲染器兜底自检全部直接索引路径；结构缺失统一"校验失败"干净报错，不裸 traceback。
    def need(cond, msg):
        if not cond:
            errs.append(msg)
    def isd(x): return isinstance(x, dict)
    def isl(x): return isinstance(x, list)
    def iss(x): return isinstance(x, str)
    def req_item(obj, keys, loc):
        if not isd(obj):
            errs.append(f"{loc} 须为对象")
            return
        for k in keys:
            if k not in obj:
                errs.append(f"{loc} 缺字段 {k}")

    def req_kn(obj, key, loc):
        """机制档位字段：仅允许字符串或 {text, sources?} 对象（对齐 schema）。
        fuzz seed 777 实证：深度嵌套数组会被引用扫描计入、但渲染端不输出，
        造成"来源存在却未被引用"的孤儿行，必须在校验期干净拒绝。"""
        if not isd(obj) or key not in obj:
            return
        v = obj[key]
        if iss(v):
            return
        if isd(v):
            if not iss(v.get("text")):
                errs.append(f"{loc}.{key}.text 缺失或非字符串")
            return
        errs.append(f"{loc}.{key} 须为字符串或对象")

    def need_list(obj, key, loc):
        # 容器字段存在但类型非数组（红队 A6 结构破坏）：显式报错，防渲染期裸崩
        if isd(obj) and key in obj and not isl(obj[key]):
            errs.append(f"{loc}.{key} 须为数组")
            return False
        return True

    def lst(x):
        # 仅当确认为数组时才迭代（红队 M3 fuzz 发现：容器字段被置换成数值/布尔时
        # "x.get(k) or []" 仍会对真值非数组迭代，裸崩 TypeError）
        return x if isinstance(x, list) else []

    need(isd(d), "根节点须为 JSON 对象")
    if errs:
        raise SystemExit("校验失败：\n" + "\n".join(" - " + e for e in errs))
    ov, sg, mc, dr, so = (d.get(k) for k in ("overview", "signals", "mechanisms", "directions", "sources"))
    need(isd(d.get("meta")), "meta 缺失或非对象")
    need(isd(ov), "overview 缺失或非对象")
    need(isd(sg), "signals 缺失或非对象")
    need(isd(mc), "mechanisms 缺失或非对象")
    need(isd(dr), "directions 缺失或非对象")
    need(isd(so), "sources 缺失或非对象")
    bu = fi = None
    if isd(ov):
        need(iss(ov.get("lead")), "overview.lead 缺失或非字符串")
        need(isl(ov.get("basic_info")), "overview.basic_info 缺失或非数组")
        need(isd(ov.get("business")), "overview.business 缺失或非对象")
        need(isd(ov.get("financial")), "overview.financial 缺失或非对象")
        bu, fi = ov.get("business"), ov.get("financial")
    if isd(bu):
        need(iss(bu.get("outline_title")), "overview.business.outline_title 缺失或非字符串")
        need(iss(bu.get("strengths_title")), "overview.business.strengths_title 缺失或非字符串")
        for k in ("outline_items", "chain", "strength_items", "moat"):
            need(isl(bu.get(k)), f"overview.business.{k} 缺失或非数组")
        # 第四轮审计 G8：heading 置换为真值非对象时渲染期 bh.get AttributeError 裸崩
        #（fuzz 种子 777/31337 共 4 用例同源此路径）；存在时须为对象，
        # id/title 渲染期直接索引故必填，nav 可选但须字符串
        if "heading" in bu and bu.get("heading") is not None and not isd(bu["heading"]):
            errs.append(f"overview.business.heading 须为对象：{bu['heading']!r}")
        if isd(bu.get("heading")):
            req_item(bu["heading"], ("id", "title"), "overview.business.heading")
            if "nav" in bu["heading"] and not iss(bu["heading"]["nav"]):
                errs.append("overview.business.heading.nav 非字符串")
    if isd(fi):
        need(iss(fi.get("lead_note")), "overview.financial.lead_note 缺失或非字符串")
        need(isl(fi.get("blocks")), "overview.financial.blocks 缺失或非数组")
    if isd(sg):
        need(iss(sg.get("lead")), "signals.lead 缺失或非字符串")
        need(iss(sg.get("dynamic_title")), "signals.dynamic_title 缺失或非字符串")
        need(isl(sg.get("key")), "signals.key 缺失或非数组")
        need(isl(sg.get("dynamic")), "signals.dynamic 缺失或非数组")
    if isd(mc):
        need(iss(mc.get("lead")), "mechanisms.lead 缺失或非字符串")
        need(isl(mc.get("items")), "mechanisms.items 缺失或非数组")
    if isd(dr):
        need(iss(dr.get("lead")), "directions.lead 缺失或非字符串")
        need(isl(dr.get("items")), "directions.items 缺失或非数组")
    if isd(so):
        need(iss(so.get("lead")), "sources.lead 缺失或非字符串")
        need(iss(so.get("homology_note")), "sources.homology_note 缺失或非字符串")
        need(isl(so.get("items")), "sources.items 缺失或非数组")
    # 逐项必填（渲染直接索引的字段；缺任一即干净拒绝）
    if isd(ov) and isl(ov.get("basic_info")):
        for i, it in enumerate(ov["basic_info"]):
            req_item(it, ("label", "value_html", "sources"), f"basic_info[{i}]")
    if isd(bu):
        for k in ("outline_items", "strength_items"):
            for i, it in enumerate(lst(bu.get(k))):
                req_item(it, ("text_html", "sources"), f"business.{k}[{i}]")
        for i, it in enumerate(lst(bu.get("chain"))):
            req_item(it, ("label", "label_bold", "text_html", "sources"), f"business.chain[{i}]")
        for i, it in enumerate(lst(bu.get("moat"))):
            req_item(it, ("label", "text_html", "sources"), f"business.moat[{i}]")
    if isd(sg):
        for i, s in enumerate(lst(sg.get("key"))):
            req_item(s, ("id", "nav", "title", "sections"), f"signals.key[{i}]")
            if isd(s) and need_list(s, "sections", f"signals.key[{i}]"):
                for j, sec in enumerate(lst(s.get("sections"))):
                    req_item(sec, ("label", "text_html", "sources"), f"signals.key[{i}].sections[{j}]")
        for i, it in enumerate(lst(sg.get("dynamic"))):
            req_item(it, ("id", "text_html", "sources"), f"signals.dynamic[{i}]")
    if isd(mc):
        for i, m in enumerate(lst(mc.get("items"))):
            req_item(m, ("id", "nav", "title", "rows", "confirmed", "unconfirmed", "evidence"), f"mechanisms.items[{i}]")
            if isd(m):
                for kn in ("confirmed", "unconfirmed", "evidence"):
                    req_kn(m, kn, f"mechanisms.items[{i}]")
            if isd(m) and need_list(m, "rows", f"mechanisms.items[{i}]"):
                for j, r in enumerate(lst(m.get("rows"))):
                    req_item(r, ("th", "td_html", "sources"), f"mechanisms.items[{i}].rows[{j}]")
    if isd(dr):
        for i, it in enumerate(lst(dr.get("items"))):
            req_item(it, ("id", "state", "title", "basis", "points"), f"directions.items[{i}]")
            # 红队 M3 fuzz：state 非法值会在渲染期 KeyError 裸崩（STATE_LABEL 映射），校验期拦截；
            # 注意必须先判 str——数组/对象置换会使 "in" 集合判重自身 unhashable 裸崩
            st = it.get("state") if isd(it) else None
            if isd(it) and (not isinstance(st, str) or st not in STATE_LABEL):
                errs.append(f"directions.items[{i}].state 非法：{st!r}（合法：{'/'.join(STATE_LABEL)}）")
            if isd(it) and need_list(it, "points", f"directions.items[{i}]"):
                for j, p in enumerate(lst(it.get("points"))):
                    req_item(p, ("label", "text_html"), f"directions.items[{i}].points[{j}]")
    if isd(so):
        # 红队 M3 fuzz：legend 被置换成标量时渲染期 TypeError 裸崩
        if "legend" in so and not isl(so["legend"]):
            errs.append("sources.legend 须为数组")
        if isl(so.get("items")):
            # 红队 M3 fuzz：渲染期对 url 做 re.match、对 url_display 做 "…" in 判断，
            # 字段被置换成数值/布尔/对象时裸崩——校验期要求来源记录全字段为字符串
            for i, it in enumerate(so.get("items") or []):
                req_item(it, ("id", "entity", "time", "caliber", "source", "url", "url_display", "fetched", "identity"),
                         f"sources.items[{i}]")
                if isd(it):
                    for k in ("id", "entity", "time", "caliber", "source", "url", "url_display", "fetched", "identity"):
                        if k in it and not iss(it[k]):
                            errs.append(f"sources.items[{i}].{k} 非字符串")
                # 红队 M3 fuzz：url2 存在而 url2_display 缺失时渲染期 KeyError 裸崩
                if isd(it) and it.get("url2") and "url2_display" not in it:
                    errs.append(f"sources.items[{i}] 缺字段 url2_display")
                # 红队 M3 fuzz：url2/url2_display 被置换成数值/数组时渲染期 re.match 裸崩（与必填字段一致要求字符串）
                if isd(it):
                    for k in ("url2", "url2_display"):
                        if k in it and not iss(it[k]):
                            errs.append(f"sources.items[{i}].{k} 非字符串")
    if isd(fi) and isl(fi.get("blocks")):
        REQ = {"table": ("caption", "header", "rows"),
               "chart_bar": ("caption", "categories", "series"),
               "timeline": ("caption", "nodes"),
               "text": ("caption", "blocks"),
               "missing": ("note",)}
        for i, b in enumerate(fi["blocks"]):
            if not isd(b) or "type" not in b:
                errs.append(f"财务块#{i} 缺字段 type")
                continue
            bt = b["type"]
            if not iss(bt):
                errs.append(f"财务块#{i} type 非字符串")
                continue
            if bt not in REQ:
                continue  # 未知类型由业务校验段报"未知块类型"
            for k in REQ[bt]:
                if k not in b:
                    errs.append(f"财务块#{i}({bt}) 缺字段 {k}")
            if bt == "chart_bar":
                for j, sr in enumerate(lst(b.get("series"))):
                    req_item(sr, ("name", "values"), f"财务块#{i}.series[{j}]")
            if bt == "timeline":
                for j, nd in enumerate(lst(b.get("nodes"))):
                    req_item(nd, ("value", "date", "who", "sources"), f"财务块#{i}.nodes[{j}]")
            if bt == "text":
                for j, blk in enumerate(lst(b.get("blocks"))):
                    req_item(blk, ("text_html", "sources"), f"财务块#{i}.blocks[{j}]")
    if errs:
        raise SystemExit("校验失败：\n" + "\n".join(" - " + e for e in errs))

    SRC_KEYS = ("sources", "caption_sources", "note_sources", "text_sources", "basis_sources")
    refs = []
    def walk(o, loc):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in SRC_KEYS:
                    # 红队 M3 fuzz：引用源字段被置换成对象/标量时须显式报错——
                    # 此前 else 分支递归会把引用静默漏检（对象）或让 sups() 裸崩（标量）。
                    # 唯一合法的"对象形 sources"是根节点的 sources 节容器（$.sources，含 items 等）。
                    if isinstance(v, list):
                        for e in v:
                            refs.append((loc + "." + k, e))
                    elif loc == "$" and k == "sources":
                        walk(v, loc + "." + k)
                    else:
                        errs.append(f"{loc}.{k} 须为数组")
                else:
                    walk(v, loc + "." + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{loc}[{i}]")
    walk(d, "$")
    declared = [it["id"] for it in d["sources"]["items"]]
    if not all(isinstance(x, str) for x in declared):
        errs.append("来源表存在非字符串编号")
        declared = [x for x in declared if isinstance(x, str)]
    dset = set(declared)
    if len(declared) != len(dset):
        errs.append("来源表存在重复编号")
    for loc, e in refs:
        # 红队 M3 fuzz：引用元素非字符串（嵌套数组/对象置换）须干净拒绝，不裸崩 re.match
        if not isinstance(e, str) or not re.match(r"^E\d+$", e) or e not in dset:
            errs.append(f"引用未声明来源 {e!r} @ {loc}")
    for e in declared:
        if e not in {x for _, x in refs if isinstance(x, str)}:
            errs.append(f"来源 {e} 从未被引用")
    navs = [s["id"] for s in d["signals"]["key"]] + [m["id"] for m in d["mechanisms"]["items"]]
    bh = d["overview"]["business"].get("heading")
    if bh and bh.get("id"):
        navs.append(bh["id"])
    # 红队 M3 fuzz：导航 id 非字符串时 set() 裸崩、含空格/引号时属性位与锚点脏污，
    # 先显式报错；合法 id 仅字母/数字/连字符/下划线（基线实例 s1-biz/sig-dyn/mech1 均满足）
    if not all(isinstance(x, str) for x in navs):
        errs.append("导航 id 存在非字符串值")
    elif not all(re.match(r"^[A-Za-z0-9_-]+$", x) for x in navs):
        errs.append("导航 id 含非法字符（仅字母/数字/-/_.）")
    elif len(navs) != len(set(navs)):
        errs.append("导航 id 重复")
    meta = d.get("meta") or {}
    for k in ("company_name", "company_short", "anchor_date"):
        if not (isinstance(meta.get(k), str) and meta[k].strip()):
            errs.append(f"meta.{k} 缺失或为空")
        # 第四轮审计 G1：数据含 sentinel 保留序列会污染徽章/精确替换（自伤型，正常研究不会出现）
        elif _SENT[:6] in meta[k]:
            errs.append(f"meta.{k} 含渲染器保留序列（非法控制字符）")
    BLOCK_TYPES = {"table", "chart_bar", "timeline", "text", "missing"}
    for i, b in enumerate(d["overview"]["financial"]["blocks"]):
        t = b.get("type")
        if not isinstance(t, str) or t not in BLOCK_TYPES:
            errs.append(f"财务块#{i} 未知块类型：{t!r}（合法：{'/'.join(sorted(BLOCK_TYPES))}）")
            continue
        if t in ("table", "chart_bar", "timeline"):
            cap = b.get("caption", "")
            pat = r"^表\d+｜" if t == "table" else r"^图\d+｜"
            # 红队 M3 fuzz：caption 置换成布尔/数值时 re.match 裸崩
            if not isinstance(cap, str):
                errs.append(f"财务块#{i}({t}) 命名行非字符串：{cap!r}")
            elif not re.match(pat, cap):
                errs.append(f"财务块#{i}({t}) 命名行不合规：{cap!r}")
        # 红队 M3 fuzz：table.rows 元素置换成标量时渲染期 r[0] 下标裸崩；
        # chart_bar series.name/unit 非字符串时拼接裸崩、color 非法时 COLORS 映射 KeyError；
        # note_sources 存在但其宿主字段（note/timeline_note）缺失或该类型不渲染它时，
        # 校验计为已引用而渲染不输出，引用闭环在产物层破坏（P3）
        if t == "table":
            if not isl(b.get("header")):
                errs.append(f"财务块#{i}(table) header 须为数组")
            if not isl(b.get("rows")):
                errs.append(f"财务块#{i}(table) rows 须为数组")
            else:
                for j, row in enumerate(b["rows"]):
                    if not isl(row):
                        errs.append(f"财务块#{i}(table) 行#{j} 须为数组")
                    elif not row:
                        errs.append(f"财务块#{i}(table) 行#{j} 为空数组（渲染期 r[0] 下标裸崩）")
            if "note_sources" in b and not b.get("note"):
                errs.append(f"财务块#{i}(table) 有 note_sources 但缺 note（引用不会被渲染）")
        if t == "chart_bar":
            if "note_sources" in b:
                errs.append(f"财务块#{i}(chart_bar) 不支持 note_sources（引用不会被渲染）")
            # 红队 M3 fuzz：series/categories 被置换成对象时渲染期迭代裸崩；元素非对象时 s["values"] 下标裸崩
            if not isl(b.get("series")):
                errs.append(f"财务块#{i}(chart_bar) series 须为数组")
            elif not b["series"]:
                errs.append(f"财务块#{i}(chart_bar) series 为空（至少 1 个序列；无数据请改用 missing 块）")
            if not isl(b.get("categories")):
                errs.append(f"财务块#{i}(chart_bar) categories 须为数组")
            for j, sr in enumerate(lst(b.get("series"))):
                if not isd(sr):
                    errs.append(f"财务块#{i} 序列#{j} 须为对象")
                    continue
                if not iss(sr.get("name")):
                    errs.append(f"财务块#{i} 序列#{j} name 非字符串")
                if "unit" in sr and not iss(sr["unit"]):
                    errs.append(f"财务块#{i} 序列#{j} unit 非字符串")
                # 先判 str——数组/对象置换会使 "in" 集合判重自身 unhashable 裸崩
                if "color" in sr and (not iss(sr["color"]) or sr["color"] not in COLORS):
                    errs.append(f"财务块#{i} 序列#{j} color 非法：{sr['color']!r}")
        if t == "timeline":
            if not isl(b.get("nodes")):
                errs.append(f"财务块#{i}(timeline) nodes 须为数组")
            if "note_sources" in b and not b.get("timeline_note"):
                errs.append(f"财务块#{i}(timeline) 有 note_sources 但缺 timeline_note（引用不会被渲染）")
        if t == "text" and not isl(b.get("blocks")):
            errs.append(f"财务块#{i}(text) blocks 须为数组")
        if t in ("text", "missing") and "note_sources" in b:
            errs.append(f"财务块#{i}({t}) 不支持 note_sources（引用不会被渲染）")
        if t == "chart_bar":
            cats = b.get("categories")
            if not isinstance(cats, list) or not cats:
                errs.append(f"财务块#{i}(chart_bar) categories 缺失或为空")
                cats = []
            for j, sr in enumerate(lst(b.get("series"))):
                vals = sr.get("values") if isinstance(sr, dict) else None
                if not isinstance(vals, list) or not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in vals):
                    errs.append(f"财务块#{i} 序列#{j} values 非有限数值数组")
                elif cats and len(vals) != len(cats):
                    errs.append(f"财务块#{i} 序列#{j} 长度({len(vals)})与 categories({len(cats)})不一致")
    def scan_sup(o, loc):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and ("_html" in k or k in ("text", "note", "timeline_note")) and "<sup" in v:
                    errs.append(f"手写 <sup> @ {loc}.{k}")
                elif isinstance(v, str) and _PLAIN_CITE_RE.search(v):
                    # 纯文本引用标记（[E9]／（E9）／(E9、E10)）不经 sources 数组，既不进闭环校验、
                    # 也不生成可点击锚点：读者看到点不动、来源表里可能也找不到的编号
                    errs.append(f"手写纯文本引用 {_PLAIN_CITE_RE.search(v).group(0)!r} @ {loc}.{k}"
                                "（改用对应字段的 sources 数组）")
                else:
                    scan_sup(v, loc + "." + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan_sup(v, f"{loc}[{i}]")
    scan_sup(d, "$")
    # 契约字段格式（schema 有、渲染器此前未执行；默认警告，--strict 阻断）：日期格式、获取日期不晚于锚点、URL 须 http(s)
    # ——非 http(s) URL 此前会静默降级为不可点击文本，读者无法溯源
    _DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    anchor = d["meta"].get("anchor_date") if isd(d.get("meta")) else None
    if not (iss(anchor) and _DATE.match(anchor)):
        warns.append(f"meta.anchor_date 须为 YYYY-MM-DD：{anchor!r}")
        anchor = None
    for i, it in enumerate(lst(d["sources"].get("items")) if isd(d.get("sources")) else []):
        if not isd(it):
            continue
        f = it.get("fetched")
        if iss(f) and not _DATE.match(f):
            warns.append(f"sources.items[{i}].fetched 须为 YYYY-MM-DD：{f!r}")
        elif iss(f) and anchor and f > anchor:
            warns.append(f"sources.items[{i}].fetched {f} 晚于锚点日期 {anchor}")
        for uk in ("url", "url2"):
            u = it.get(uk)
            if uk in it and not (iss(u) and re.match(r"^https?://\S+$", u, re.I)):
                warns.append(f"sources.items[{i}].{uk} 须为完整 http(s) URL：{u!r}")
    # 4.0 引用覆盖（schema：basis_sources「建议尽调场景必挂」、points.sources「建议必挂」）：
    # 不阻断——方向可以是推断——但逐方向汇总未挂来源的条目，提醒补挂或在措辞中标明推断
    for it in lst(d["directions"].get("items")) if isd(d.get("directions")) else []:
        if not isd(it):
            continue
        pts = [p for p in lst(it.get("points")) if isd(p)]
        bare = sum(1 for p in pts if not p.get("sources"))
        if not it.get("basis_sources") or bare:
            warns.append(f"4.0 {it.get('id')}：basis {'未' if not it.get('basis_sources') else '已'}挂来源，"
                         f"{bare}/{len(pts)} 条要点未挂来源（属推断请在措辞中标明并给依据）")
    bi = d["overview"]["basic_info"]
    exp = ["公司全称", "官网", "成立时间", "注册地／经营地", "所有制／资本状态", "高管背景", "员工规模", "组织结构"]
    labels = [x["label"] for x in bi]
    # 红队 M3 fuzz：label 被置换成数组/对象时 set() 裸崩，先显式报错
    if not all(isinstance(x, str) for x in labels):
        errs.append("basic_info 存在非字符串 label")
        labels = [x for x in labels if isinstance(x, str)]
    if labels[:len(exp)] != exp:
        errs.append("basic_info 前 8 项核心清单不合规（须按序）")
    if len(set(labels)) != len(labels):
        errs.append("basic_info 存在重复 label")
    order = ["业务任务", "业务系统", "功能需求", "负载特性", "运行方式", "对业务结果的影响", "关联的 IT 能力"]
    for m in d["mechanisms"]["items"]:
        if [r["th"] for r in m["rows"]] != order:
            errs.append(f"{m['id']} 七行不合规")
    for s in d["signals"]["key"]:
        if [x["label"] for x in s["sections"]] != ["事实依据", "为什么重要", "对关注方向的影响"]:
            errs.append(f"{s['id']} 三段不合规")
    if strict:
        errs += warns
        warns = []
    if errs:
        raise SystemExit("校验失败：\n" + "\n".join(" - " + e for e in errs))
    WARNS[:] = warns
    return warns

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
            chart_scroll(chart_svg(n, b)),
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

# ---- 柱图布局 v2（评审补丁 0010）：先算各元素包围盒、再定坐标，结构上保证不重叠 ----
# 根因（171e1bc 及更早版本均存在）：① 图例固定画在 y≈10–20，绘图区顶 y=32 与之只隔 12px，
#   且纵轴上限只把最大值向上取整到 10 的倍数，最高柱几乎顶到 y=32，数值标签（基线 y-6、字高约 9px）
#   落进图例行；② 数值标签左对齐于柱左缘，"1695.00"约 46px 宽而每柱槽位仅 36px（柱宽 30＋间距 6），
#   多序列时标签压到相邻柱和相邻标签；③ 图例按固定 150px 步进不换行，长名称互相覆盖；
#   ④ 负值标签画在柱底下方 13px，可压到 y=222 的类目文字。
_CH_FS, _CH_LH = 12, 13          # 数值标签字号与行高（字面高度约 9px，留 4px 余量）

def _tw(s, fs):
    """文本宽度保守估计（SVG 用户坐标）。系数按 headless Chrome＋Noto Sans/Noto CJK 实测 getBBox 标定并上浮，
    Windows（微软雅黑/Segoe UI）与 macOS（苹方）字形更窄，估计值只会偏大、不会偏小。"""
    w = 0.0
    for ch in str(s):
        o = ord(ch)
        if o >= 0x2E80 or 0xFF00 <= o <= 0xFFEF:
            w += 1.15
        elif ch in ".,:;'!|ij l":
            w += 0.36
        elif ch in "-()/":
            w += 0.45
        elif ch.isdigit():
            w += 0.66
        elif ch.isupper():
            w += 0.82
        else:
            w += 0.64
    return w * fs

_CHART_MIN_PX = 11  # 屏幕上图内最小字号（CSS px），经用户确认取 11px

def chart_scroll(svg):
    """把柱图 <svg> 包进 <div class="chart-scroll">（窄屏横向滚动）。
    按画布宽 W 与图内最小字号 fs 算出 --chart-minw = ceil(W*11/fs)：svg 被 max-width:100% 缩放后，
    渲染宽度不低于该值即可保证最小字号 ≥11px。min-width 只在单栏版式（≤920px，见骨架 CSS）生效，
    带侧栏的桌面版式不受影响（≥1000px 截图与此前逐像素一致）。W 取 0010 动态画布的 viewBox 宽。"""
    W = float(re.search(r'viewBox="0 0 ([\d.]+) ', svg).group(1))
    fs = min(float(x) for x in re.findall(r'font-size="([\d.]+)"', svg))
    minw = -(-int(W * _CHART_MIN_PX * 100) // int(fs * 100))  # 整数运算向上取整，避免浮点误差
    svg = svg.replace('style="margin:6px 0 4px; max-width:100%;"',
                      f'style="margin:6px 0 4px; max-width:100%; --chart-minw:{minw}px;"', 1)
    return '<div class="chart-scroll">' + svg + '</div>'

def chart_svg(n, b):
    cats, series = b["categories"], b["series"]
    nc, ns = len(cats), len(series)
    ints = all(isinstance(v, int) for s in series for v in s["values"])
    def fmt(v):  # 计数类整数不补 .00；≥1 万加千分位（基线数据均 <1 万，文本不变）
        f = "{:,.0f}" if ints else "{:,.2f}"
        return (f if abs(v) >= 10000 else f.replace(",", "")).format(v)
    labels = [[fmt(v) for v in s["values"]] for s in series]
    maxv = max(max(s["values"]) for s in series)
    minv = min(min(s["values"]) for s in series)
    names = [s["name"] for s in series]
    aria = f"图{n} {'与'.join(names)}柱状图（{cats[0]}–{cats[-1]}）"
    # 水平：每柱槽位 ≥ 最宽数值标签＋4，标签居中于柱心 → 组内标签、相邻柱互不覆盖
    bw, x0 = 30, 70
    sw = max(36, max(_tw(t, _CH_FS) for row in labels for t in row) + 4)
    group_w = ns * sw
    catw = max(_tw(c, 12.5) for c in cats)
    need = max(group_w + 14, catw + 8)
    W = 660
    gw = max(need, min(140, (W - x0 - 20) / nc))
    W = max(W, int(x0 + gw * nc + 20 + 0.999))
    # 图例：按实际文字宽度排布，超出可用宽度自动换行
    items = [(s, esc(s["name"] + (f'（{s["unit"]}）' if s.get("unit") else "")),
              16 + _tw(s["name"] + (f'（{s["unit"]}）' if s.get("unit") else ""), 12) + 20) for s in series]
    rows, cur, cw = [], [], 0.0
    for it in items:
        if cur and x0 + cw + it[2] > W - 10:
            rows.append(cur); cur, cw = [], 0.0
        cur.append(it); cw += it[2]
    rows.append(cur)
    W = max(W, int(max(x0 + sum(i[2] for i in r) for r in rows) + 10.999))
    legend_end = 10 + 18 * len(rows)                 # 图例带底（最后一行色块底 y=legend_end-8）
    plot_top = legend_end + _CH_LH + 4               # 预留一行数值标签高度：最高柱标签必在图例带之下
    plot_h = 160
    neg = minv < 0
    base_y = plot_top + plot_h                       # 绘图区底
    cat_y = base_y + (_CH_LH + 6 if neg else 0) + 22 # 负值标签占用绘图区下方一行，类目文字再下移
    H = cat_y + 28
    # data-md：图表数据的 Markdown 表，供骨架"导出 MD"输出数值
    def _md(x):
        return str(x).replace("|", "\\|").replace("\n", " ")
    hdr = ["类目"] + [_md(s["name"] + (f'（{s["unit"]}）' if s.get("unit") else "")) for s in series]
    md_rows = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for i, c in enumerate(cats):
        md_rows.append("| " + " | ".join([_md(c)] + [labels[j][i] for j in range(ns)]) + " |")
    data_md = esc_attr("\n".join(md_rows))
    el = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc_attr(aria)}" data-md="{data_md}" style="margin:6px 0 4px; max-width:100%;">']
    for r_i, r in enumerate(rows):
        lx, ly = x0, 10 + 18 * r_i
        for s, txt, w in r:
            c = COLORS[s.get("color", "blue")]
            el.append(f'    <rect x="{round(lx, 1)}" y="{ly}" width="10" height="10" fill="{c}" rx="2"/>')
            el.append(f'    <text x="{round(lx + 16, 1)}" y="{ly + 9}" font-size="12" fill="#1f2733">{txt}</text>')
            lx += w
    hi = max(maxv, 0)
    lo = min(minv, 0)
    span = (hi - lo) or 1
    k = plot_h / span
    zero_y = plot_top + hi * k
    for i in range(nc):
        gx = x0 + gw * i + (gw - group_w) / 2
        for j, s in enumerate(series):
            v = s["values"][i]
            c = COLORS[s.get("color", "blue")]
            bx = gx + j * sw + (sw - bw) / 2
            cx = round(bx + bw / 2, 1)
            h = round(abs(v) * k, 1)
            if v >= 0:
                y = round(zero_y - h, 1)
                ly = int(y - 5)                      # 柱顶上方：基线距柱顶 5px，不触柱
            else:
                y = round(zero_y, 1)
                ly = int(y + h + _CH_LH + 3)         # 柱底下方一行（CJK 字体上伸部较高，留足 3px），落在预留的下方标签带内
            el.append(f'    <rect x="{round(bx, 1)}" y="{y}" width="{bw}" height="{h}" fill="{c}" rx="2"/>')
            el.append(f'    <text x="{cx}" y="{ly}" font-size="12" fill="{c}" text-anchor="middle">{labels[j][i]}</text>')
    zy = round(zero_y, 1)
    el.append(f'    <line x1="50" y1="{zy}" x2="{W - 20}" y2="{zy}" stroke="{"#1f2733" if neg else "#e3e8ef"}" stroke-width="1.5"/>')
    for i, c in enumerate(cats):
        el.append(f'    <text x="{round(x0 + gw * i + gw / 2, 1)}" y="{cat_y}" font-size="12.5" fill="#1f2733" text-anchor="middle">{esc(c)}</text>')
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
        L.append(f'  <h3 class="block-title" id="{esc_attr(h["id"])}">{esc(h["title"])}</h3>')
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
        L.append(f'  <div class="signal" id="{esc_attr(sig["id"])}">')
        L.append(f'    <h4>{esc(sig["title"])}</h4>')
        for sec in sig["sections"]:
            L.append(f'    <p><span class="lbl">{esc(sec["label"])}：</span>{rich(sec["text_html"])}{sups(sec["sources"])}</p>')
        L.append("  </div>")
    dyn_id = ' id="sig-dyn"' if s.get("dynamic_nav") else ""
    L.append(f'  <h3 class="block-title"{dyn_id}>{esc(s["dynamic_title"])}</h3>')
    L.append('  <ul class="dyn-list">')
    for it in s["dynamic"]:
        date = f'{esc(it["date"])}｜' if it.get("date") else ""
        L.append(f'    <li><b>{esc(it["id"])}</b>｜{date}{rich(it["text_html"])}{sups(it["sources"])}</li>')
    L.append("  </ul>")
    L.append('  <div class="export-row"><button class="export-btn" data-sec="p2" data-name="2.0经营事件与信号" title="导出为 Markdown 文件">导出 MD</button></div>')
    L.append("</section>")
    return "\n".join(L)

def render_p3(d):
    L = ['<section class="page" id="p3">',
         '  <div class="page-title"><span class="no">3.0</span><span>业务及技术解析</span></div>',
         f'  <div class="page-lead">{esc(d["mechanisms"]["lead"])}</div>']
    for m in d["mechanisms"]["items"]:
        L.append(f'  <div class="mech" id="{esc_attr(m["id"])}">')
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
        L.append(f'    <div class="basis">{esc(it["basis"])}{sups(it.get("basis_sources"))}</div>')
        for p in it["points"]:
            L.append(f'    <p><span class="lbl">{esc(p["label"])}：</span>{rich(p["text_html"])}{sups(p.get("sources"))}</p>')
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
        if url and re.match(r"^https?://", url, re.I):
            return f'<a href="{esc_href(url)}" target="_blank"{title}>{esc(display)}</a>'
        return esc(display)
    for it in s["items"]:
        title = ' title="该来源链接在研究记录中不完整，溯源至网站首页"' \
            if ("…" in it["url_display"] and re.match(r"^https?://[^/?#]+/?$", it["url"])) else ""
        href = src_link(it["url"], it["url_display"], title)
        if it.get("url2"):
            href += src_link(it["url2"], it["url2_display"])
        L.append(f'    <tr id="{esc_attr(it["id"])}"><td class="eid">{it["id"]}</td><td>{esc(it["entity"])}</td>'
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
        L.append(f'    <a class="sub" href="#{esc_attr(bh["id"])}" data-t="{esc_attr(bh["nav"])}">{esc(bh["nav"])}</a>')
    L.append('    <a class="sub" href="#s1-fin" data-t="财务数据">财务数据</a>')
    L.append('    <a class="grp" href="#p2" data-t="经营事件与信号">经营事件与信号</a>')
    for sig in s["key"]:
        L.append(f'    <a class="sub" href="#{esc_attr(sig["id"])}" data-t="{esc_attr(sig["nav"])}">{esc(sig["nav"])}</a>')
    if s.get("dynamic_nav"):
        L.append(f'    <a class="sub" href="#sig-dyn" data-t="{esc_attr(s["dynamic_nav"])}">{esc(s["dynamic_nav"])}</a>')
    L.append('    <a class="grp" href="#p3" data-t="业务及技术解析">业务及技术解析</a>')
    for mech in m["items"]:
        L.append(f'    <a class="sub" href="#{esc_attr(mech["id"])}" data-t="{esc_attr(mech["nav"])}">{esc(mech["nav"])}</a>')
    L.append('    <a class="grp" href="#p4" data-t="IT关注方向及跟进">IT关注方向及跟进</a>')
    L.append('    <a class="grp" href="#p5" data-t="来源索引与证据链">来源索引与证据链</a>')
    return "\n".join(L)

# ---------- 主流程 ----------
def main():
    strict = "--strict" in sys.argv[1:]
    args = [a for a in sys.argv[1:] if a != "--strict"]
    data_p, skel_p, out_p = args[0], args[1], args[2]
    d = json.load(open(data_p, encoding="utf-8"))
    warns = validate(d, strict=strict)
    for w in warns:
        print(f"校验警告：{w}", file=sys.stderr)
    meta = d["meta"]
    skel = pathlib.Path(skel_p).read_text(encoding="utf-8")
    body = "\n\n".join([render_p1(d), render_p2(d), render_p3(d), render_p4(d), render_p5(d)])
    # Logo 徽章：短名超 2 字时按行数自适应缩字号（两字输出与历史基线逐字节一致）
    short = meta["company_short"]
    lines = -(-len(short) // 2)  # 每行最多 2 字
    fs = min(20, max(9, int(40 // (1.15 * lines))))
    badge = (f'<div class="logo-badge" style="font-size:{fs}px; line-height:1.15;">{esc(short)}</div>'
             if fs < 20 else f'<div class="logo-badge">{esc(short)}</div>')
    # 红队 A4：骨架含 JS 字符串语境的令牌，先做精确替换（esc_js），其余按 HTML 语境转义
    # 红队 M4 A8：全部令牌改单次扫描替换——插入值不再参与后续扫描，数据中的
    # 令牌字面量原样留在产物（防二次替换/交叉污染，如 company_name 含 {{SHORT}}）；
    # 需特殊语境的精确替换目标（JS 串/徽章）先用 sentinel 保护，其插入值同样不参与扫描。
    # 基线数据不含令牌字面量，输出与逐次 replace 链逐字节一致（等价比对锁定）。
    precise = [("企业研究_{{SHORT}}_", "企业研究_" + esc_js(short) + "_"),
               ("企业研究报告：{{COMPANY_NAME}}", "企业研究报告：" + esc_js(meta["company_name"])),
               ("锚点日期 {{ANCHOR_DATE}}；", "锚点日期 " + esc_js(meta["anchor_date"]) + "；")]
    skel = skel.replace('<div class="logo-badge">{{SHORT}}</div>', _SENT % 0)
    for i, (tok, _) in enumerate(precise, start=1):
        skel = skel.replace(tok, _SENT % i)
    # 第四轮审计 G3：precise 锚点对骨架文案隐式耦合——锚点失配时此前静默退化为
    # HTML 语境替换，JS 串语境 esc 失效（短名含引号可未转义直通）。冻结产物原则：
    # 骨架与渲染器必须同源交付，锚点缺失＝版本 skew，干净报错不出半成品。
    miss_anchor = [_SENT % i for i in range(4) if (_SENT % i) not in skel]
    if miss_anchor:
        raise SystemExit("骨架与渲染器不匹配：精确语境锚点缺失（徽章 div/JS 串令牌），"
                         "skeleton.html 为冻结产物，改版须与渲染器同源改版并同步交付")
    mapping = {"COMPANY_NAME": esc(meta["company_name"]),
               "SAMPLE_VERSION": esc(meta.get("sample_version", "")),
               "SHORT": esc(short),
               "ANCHOR_DATE": esc(meta["anchor_date"]),
               "SEARCH_HINT": esc_attr(meta.get("search_hint", "输入关键词……")),
               "SIDENAV": render_sidenav(d),
               "BODY": body}
    out = re.sub(r"\{\{(COMPANY_NAME|SAMPLE_VERSION|SHORT|ANCHOR_DATE|SEARCH_HINT|SIDENAV|BODY)\}\}",
                 lambda mo: mapping[mo.group(1)], skel)
    out = out.replace(_SENT % 0, badge)
    for i, (_, val) in enumerate(precise, start=1):
        out = out.replace(_SENT % i, val)
    # 双臂验证工程复验缺陷 A：write_text 在 Windows 会把 \n 转成 CRLF，导致打印的
    # UTF-8 字节数与落盘字节数不一致，也破坏跨平台逐字节等价。按字节写盘固定 LF。
    pathlib.Path(out_p).write_bytes(out.encode("utf-8"))
    print(f"渲染完成：{out_p}（{len(out.encode('utf-8'))} 字节）")

if __name__ == "__main__":
    main()
