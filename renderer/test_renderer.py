# -*- coding: utf-8 -*-
"""
渲染器回归与攻击面测试 v1.0（零第三方依赖，Python 3.8+ 标准库）
用法:
  python test_renderer.py                    # 攻击面＋结构自检（无需基线样张）
  python test_renderer.py <基线1.html> [基线2.html …]   # 另跑等价比对回归
数据发现顺序：../examples/、./examples/、脚本上级目录、当前目录（找含 "mechanisms" 的 JSON）
基线缺省时自动尝试 ../samples/*.html。
退出码：0 全过；1 有失败项。
"""
import json, re, subprocess, sys, copy, tempfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
RENDER = ROOT / "render.py"
SKEL = ROOT / "skeleton.html"

def run_render(data):
    with tempfile.TemporaryDirectory() as td:
        jp = pathlib.Path(td) / "in.json"
        hp = pathlib.Path(td) / "out.html"
        jp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(RENDER), str(jp), str(SKEL), str(hp)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        html = hp.read_text(encoding="utf-8") if hp.exists() else ""
        return r, html

def looks_like_report(p):
    if "schema" in p.name.lower():
        return False
    try:
        head = p.read_text(encoding="utf-8", errors="ignore")[:200000]
    except OSError:
        return False
    return '"meta"' in head and '"mechanisms"' in head

def find_examples():
    cands = [ROOT.parent / "examples", ROOT / "examples", ROOT.parent, pathlib.Path.cwd()]
    for c in cands:
        if not c.is_dir():
            continue
        files = [f for f in sorted(c.glob("*.json")) if looks_like_report(f)]
        if files:
            return files[:2]
    return []

def find_baselines(argv):
    if argv:
        return [pathlib.Path(a) for a in argv]
    for c in [ROOT.parent / "samples", ROOT / "samples"]:
        if c.is_dir():
            files = sorted(c.glob("*.html"))
            if files:
                return files
    return []

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"  {'✓' if ok else '✗'} {name}" + (f" — {detail}" if detail and not ok else ""))

def load_example():
    files = find_examples()
    if not files:
        raise SystemExit("未找到数据实例 JSON（examples/ 或上级目录）")
    return files, json.loads(files[0].read_text(encoding="utf-8"))

def main():
    print("== 攻击面与健壮性 ==")
    files, base_data = load_example()

    t = copy.deepcopy(base_data); t["overview"]["financial"]["blocks"][0]["type"] = "note"
    r, _ = run_render(t)
    check("H2 未知块类型(note) 干净拒绝", r.returncode != 0 and "未知块类型" in (r.stderr or ""), (r.stderr or "")[-120:])

    def find_chart(t):
        for b in t["overview"]["financial"]["blocks"]:
            if b.get("type") == "chart_bar":
                return b
        return None

    def add_chart(t, cats, series, caption="图9｜攻击面测试"):
        t["overview"]["financial"]["blocks"].append(
            {"type": "chart_bar", "caption": caption, "categories": cats, "series": series})

    t = copy.deepcopy(base_data)
    cb = find_chart(t)
    if cb is None:
        add_chart(t, ["2023", "2024"], [{"name": "净利", "values": [-1.5, -2.5]}])
    else:
        for s in cb["series"]:
            s["values"] = [-abs(v) for v in s["values"]]
    r, html = run_render(t)
    check("H1 负值图表正常渲染", r.returncode == 0 and 'height="-' not in html,
          "崩溃或仍有负高度" if r.returncode == 0 else (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    t["overview"]["lead"] = "x<script>alert(1)</script>"
    r, html = run_render(t)
    check("H3 <script> 注入被转义", r.returncode == 0 and "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html)

    t = copy.deepcopy(base_data)
    t["sources"]["items"][0]["url"] = "javascript:alert(1)"
    r, html = run_render(t)
    check("H3 javascript: URL 降级为文本", r.returncode == 0 and 'href="javascript:' not in html)

    t = copy.deepcopy(base_data); del t["meta"]["company_name"]
    r, _ = run_render(t)
    check("M1 缺 meta 干净拒绝", r.returncode != 0 and "meta.company_name" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    cb = find_chart(t)
    if cb is None:
        add_chart(t, ["2024", "2025"], [{"name": "营收", "values": [1.0, 1.0]}])
        t["overview"]["financial"]["blocks"][-1]["series"][0]["values"] = [1.0]
    else:
        cb["series"][0]["values"] = cb["series"][0]["values"][:-1]
    r, _ = run_render(t)
    check("M2 序列长度不一致拒绝", r.returncode != 0 and "长度" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    cb = find_chart(t)
    if cb is None:
        add_chart(t, [], [{"name": "营收", "values": [1.0]}])
    else:
        cb["categories"] = []
    r, _ = run_render(t)
    check("M2 categories 为空拒绝", r.returncode != 0 and "categories" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    cb = find_chart(t)
    if cb is None:
        add_chart(t, ["2024", "2025"], [{"name": "营收", "values": ["abc", "abc"]}])
    else:
        cb["series"][0]["values"] = ["abc"] * len(cb["categories"])
    r, _ = run_render(t)
    check("M2 values 非数值拒绝", r.returncode != 0 and "数值" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data); t.get("sources", {}).pop("legend", None)
    r, _ = run_render(t)
    check("H4 缺 sources.legend 不崩", r.returncode == 0, (r.stderr or "")[-120:])

    def rich_probe(t, payload):
        # overview.lead 走 esc() 纯转义通道；白名单通道是 rich()——
        # 取 4.0 方向 points[].text_html（经 rich 处理）做探针
        t["directions"]["items"][0]["points"][0]["text_html"] = payload
        return t

    t = rich_probe(copy.deepcopy(base_data), "正常<b>加粗</b>直通")
    r, html = run_render(t)
    check("白名单 <b> 直通（正例）", r.returncode == 0 and "<b>加粗</b>" in html)

    t = rich_probe(copy.deepcopy(base_data), 'x<a href="javascript:alert(1)">链</a>')
    r, html = run_render(t)
    check("H3 _html 内危险 href 剥离", r.returncode == 0 and 'href="javascript:' not in html and "<a>链</a>" in html)

    t = copy.deepcopy(base_data); t["meta"]["company_short"] = "词元无限"
    r, html = run_render(t)
    m = re.search(r'logo-badge[^>]*style="font-size:(\d+)px', html)
    ok = r.returncode == 0 and m and int(m.group(1)) < 20
    check("Logo 徽章 4 字短名自适应缩字号", ok, f"font-size={m.group(1) if m else '无 style'}")

    # ---- 二次实测修复项（N1/N2/N8） ----
    t = copy.deepcopy(base_data)
    t["directions"]["items"][0]["basis_sources"] = ["E1"]
    t["directions"]["items"][0]["points"][0]["sources"] = ["E2"]
    t["signals"]["dynamic"][0]["date"] = "2025-07"
    r, html = run_render(t)
    ok = (r.returncode == 0 and html.count('class="src"') >= 2
          and "2025-07｜" in html)
    check("N1 directions 挂来源＋N8 dynamic date 渲染", ok, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    # 扩展项 label 须在任意基准实例中唯一（模思实例已含 注册资本/统一社会信用代码 扩展项）
    t["overview"]["basic_info"].append({"label": "参保人数", "value_html": "120 人", "sources": ["E1"]})
    r, html = run_render(t)
    check("N2 basic_info 追加尽调扩展项", r.returncode == 0 and "参保人数" in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    t["overview"]["basic_info"] = t["overview"]["basic_info"][1:]
    r, _ = run_render(t)
    check("N2 核心 8 项缺项仍拒绝", r.returncode != 0 and "basic_info" in (r.stderr or ""), (r.stderr or "")[-120:])

    # ---- 第三轮审计修复项（F13/F1/F2/F3/F8，2026-10-22，契约/测试/代码同源交付）----
    t = copy.deepcopy(base_data)
    for b in t["overview"]["financial"]["blocks"]:
        if b.get("type") == "table":
            b["caption"] = re.sub(r"^表(\d+)｜", r"图\1｜", b["caption"])
            break
    else:
        t["overview"]["financial"]["blocks"].append({"type": "table", "caption": "图9｜测试", "header": ["项目", "数值"], "rows": [["a", "b"]]})
    r, _ = run_render(t)
    check("F13 table 命名行 图N｜ 干净拒绝（契约对齐渲染器）", r.returncode != 0 and "命名行" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    # 扩展项 label 须在任意基准实例中唯一（模思实例已含 注册资本/统一社会信用代码 扩展项）
    t["overview"]["basic_info"].append({"label": "股东／实控人", "value_html": "公开披露未显示实控人变更", "sources": ["E1"]})
    t["overview"]["basic_info"].append({"label": "变更记录", "value_html": "2026-03 注册资本变更一次", "sources": ["E1"]})
    r, html = run_render(t)
    check("F1 basic_info 核心 8 项后可追加多条尽调扩展项", r.returncode == 0 and "股东／实控人" in html, (r.stderr or "")[-120:])

    f3_cases = []
    t0 = copy.deepcopy(base_data); t0.pop("signals")
    f3_cases.append(("signals 缺失", t0))
    t0 = copy.deepcopy(base_data); t0["overview"].pop("basic_info")
    f3_cases.append(("basic_info 缺失", t0))
    t0 = copy.deepcopy(base_data); t0["sources"].pop("homology_note")
    f3_cases.append(("sources.homology_note 缺失", t0))
    t0 = copy.deepcopy(base_data); t0["signals"].pop("dynamic_title")
    f3_cases.append(("signals.dynamic_title 缺失", t0))
    t0 = copy.deepcopy(base_data)
    t0["overview"]["financial"]["blocks"].append({"type": "text", "blocks": [{"text_html": "段落", "sources": ["E1"]}]})
    f3_cases.append(("text 块缺 caption", t0))
    t0 = copy.deepcopy(base_data)
    t0["overview"]["financial"]["blocks"].append({"type": "timeline", "caption": "图9｜测试", "nodes": [{"value": "v", "date": "2026-01", "sources": ["E1"]}]})
    f3_cases.append(("timeline 节点缺 who", t0))
    t0 = copy.deepcopy(base_data)
    for b in t0["overview"]["financial"]["blocks"]:
        if b.get("type") == "chart_bar" and b.get("series"):
            b["series"][0].pop("name")
            break
    else:
        t0["overview"]["financial"]["blocks"].append({"type": "chart_bar", "caption": "图9｜测试", "categories": ["2024"], "series": [{"values": [1]}]})
    f3_cases.append(("chart 序列缺 name", t0))
    for name, t in f3_cases:
        r, _ = run_render(t)
        err = r.stderr or ""
        ok = r.returncode != 0 and "校验失败" in err and "Traceback" not in err
        check("F3 结构缺失干净拒绝：%s" % name, ok, err[-160:])

    t = copy.deepcopy(base_data)
    injected = False
    for b in t["overview"]["financial"]["blocks"]:
        if b.get("type") == "chart_bar" and b.get("series"):
            b["series"][0]["name"] = 'x" onmouseover="alert(1)'
            injected = True
            break
    if not injected:
        t["overview"]["financial"]["blocks"].append({"type": "chart_bar", "caption": "图9｜测试", "categories": ["2024"], "series": [{"name": 'x" onmouseover="alert(1)', "values": [1]}]})
    r, html = run_render(t)
    check("F2 属性位双引号转义（aria-label/data-t 注入防护）",
          r.returncode == 0 and 'onmouseover="alert(1)"' not in html and "&quot;" in html,
          (r.stderr or "")[-120:] if r.returncode != 0 else "属性突破未转义")

    t = rich_probe(copy.deepcopy(base_data), "x<a href='https://example.com/a'>链</a>")
    r, html = run_render(t)
    check("F8 _html 单引号 href 兼容", r.returncode == 0 and '<a href="https://example.com/a" target="_blank">链</a>' in html)

    # ---- 红队 M1（D-88 批准）：A4 属性/文本/JS 三语境注入 · A3 白名单变形 · A5 scheme 变体 ----
    INJ = 'x" onmouseover="PWNED(1)'
    a4_cases = []
    t0 = copy.deepcopy(base_data); t0["meta"]["company_name"] = INJ + "</title><script>PWNED(1)</script>"
    a4_cases.append(("meta.company_name（标题/正文/JS 三语境）", t0, ["<script>PWNED(1)</script>", ' onmouseover="PWNED(1)"']))
    t0 = copy.deepcopy(base_data); t0["meta"]["company_short"] = INJ
    a4_cases.append(("meta.company_short（徽章/JS 文件名词境）", t0, [' onmouseover="PWNED(1)"']))
    t0 = copy.deepcopy(base_data); t0["meta"]["search_hint"] = INJ
    a4_cases.append(("meta.search_hint（placeholder 属性语境）", t0, [' onmouseover="PWNED(1)"']))
    t0 = copy.deepcopy(base_data); t0["signals"]["key"][0]["nav"] = INJ
    a4_cases.append(("signals.key[0].nav（data-t 属性语境）", t0, [' onmouseover="PWNED(1)"']))
    t0 = copy.deepcopy(base_data); t0["mechanisms"]["items"][0]["nav"] = INJ
    a4_cases.append(("mechanisms.items[0].nav（data-t 属性语境）", t0, [' onmouseover="PWNED(1)"']))
    t0 = copy.deepcopy(base_data); t0["sources"]["items"][0]["entity"] = INJ
    a4_cases.append(("sources.items[0].entity（表格单元格）", t0, [' onmouseover="PWNED(1)"']))
    t0 = copy.deepcopy(base_data); t0["directions"]["items"][0]["title"] = INJ
    a4_cases.append(("directions.items[0].title", t0, [' onmouseover="PWNED(1)"']))
    a4_bad = []
    for name, t, raw_tokens in a4_cases:
        r, html = run_render(t)
        if r.returncode != 0 or any(tok in html for tok in raw_tokens):
            a4_bad.append(name)
    check("A4 注入八字段扫描（属性/文本/JS 三语境）", not a4_bad, "；".join(a4_bad)[:160])

    t = copy.deepcopy(base_data); t["meta"]["company_short"] = 'x";PWNED(1);//'
    r, html = run_render(t)
    check("A4 JS 字符串语境转义（下载文件名/MD 导出头）",
          r.returncode == 0 and 'x\\";PWNED(1);//' in html)

    t = copy.deepcopy(base_data); t["meta"]["anchor_date"] = '2026-01-01";PWNED(1);//'
    r, html = run_render(t)
    check("A4 anchor_date JS 串转义",
          r.returncode == 0 and '2026-01-01\\";PWNED(1);//' in html)

    a3_cases = [
        ("大写标签", "正常<B>加粗</B>直通", "<b>加粗</b>"),
        ("href 多空格", 'x<a  href="https://example.com">链</a>', '<a href="https://example.com" target="_blank">链</a>'),
        ("未知标签转义", "x<img src=x onerror=PWNED(1)>尾", "&lt;img"),
        ("危险 href 剥离", 'x<a href="javascript:PWNED(1)">链</a>', "<a>链</a>"),
        ("白名单嵌套", 'x<a href="https://example.com"><b>粗</b></a>', '<a href="https://example.com" target="_blank"><b>粗</b></a>'),
    ]
    for name, payload, expect in a3_cases:
        t = rich_probe(copy.deepcopy(base_data), payload)
        r, html = run_render(t)
        check("A3 白名单变形：%s" % name, r.returncode == 0 and expect in html)

    t = copy.deepcopy(base_data)
    t["sources"]["items"][0]["url"] = "HTTPS://EXAMPLE.COM/A"
    r, html = run_render(t)
    check("A5 scheme 大小写兼容（HTTPS 大写不降级）", r.returncode == 0 and 'href="HTTPS://EXAMPLE.COM/A"' in html)

    t = copy.deepcopy(base_data)
    t["sources"]["items"][0]["url"] = 'https://example.com/"onmouseover="PWNED(1)'
    r, html = run_render(t)
    check("A5 URL 内嵌引号不突破属性", r.returncode == 0 and 'onmouseover="PWNED(1)"' not in html)

    # ---- 红队 M2（计划 v0.1 已批准）：A1 输入变异 · A6 结构破坏 · A7 图表边界 ----
    t = copy.deepcopy(base_data)
    cb = find_chart(t)
    if cb is None:
        add_chart(t, ["2024"], [{"name": "n", "values": [1]}])
        cb = t["overview"]["financial"]["blocks"][-1]
    cb["series"][0]["values"] = [float("nan")] * len(cb["categories"])
    r, _ = run_render(t)
    check("A7 NaN 数值干净拒绝", r.returncode != 0 and "数值" in (r.stderr or "") and "Traceback" not in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    cb = find_chart(t)
    if cb is None:
        add_chart(t, ["2024"], [{"name": "n", "values": [1]}])
        cb = t["overview"]["financial"]["blocks"][-1]
    cb["series"][0]["values"] = [float("inf")] * len(cb["categories"])
    r, _ = run_render(t)
    check("A7 Inf 数值干净拒绝", r.returncode != 0 and "数值" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    add_chart(t, ["2022", "2023", "2024"], [{"name": "零值序列", "values": [0, 0, 0]}])
    r, html = run_render(t)
    check("A7 全零序列正常渲染", r.returncode == 0, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    add_chart(t, ["2022", "2023"], [{"name": "微小值", "values": [0.001, 0.002]}, {"name": "巨大值", "values": [1e9, 2e9]}])
    r, html = run_render(t)
    check("A7 跨数量级混合序列", r.returncode == 0 and 'height="-' not in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    add_chart(t, ["2024"], [{"name": "s%d" % i, "values": [i]} for i in range(20)])
    r, html = run_render(t)
    check("A7 20 序列不崩", r.returncode == 0, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    add_chart(t, ['<img src=x onerror=PWNED(1)>', "2025"], [{"name": "n", "values": [1, 2]}])
    r, html = run_render(t)
    check("A7 categories 含 HTML 被转义", r.returncode == 0 and "<img src=x" not in html and "&lt;img" in html)

    t = copy.deepcopy(base_data); t["meta"] = ["not", "a", "dict"]
    r, _ = run_render(t)
    check("A6 meta 类型置换干净拒绝", r.returncode != 0 and "校验失败" in (r.stderr or "") and "Traceback" not in (r.stderr or ""), (r.stderr or "")[-120:])

    a6_swap = []
    t0 = copy.deepcopy(base_data); t0["overview"]["basic_info"] = {"label": "x"}
    a6_swap.append(("basic_info 对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["signals"]["key"] = "sig1"
    a6_swap.append(("signals.key 字符串置换", t0))
    t0 = copy.deepcopy(base_data); t0["signals"]["key"][0]["sections"] = {"label": "事实依据", "text_html": "x", "sources": ["E1"]}
    a6_swap.append(("sections 对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["mechanisms"]["items"][0]["rows"] = {"th": "业务任务", "td_html": "x", "sources": ["E1"]}
    a6_swap.append(("mech rows 对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["directions"]["items"][0]["points"] = {"label": "说明", "text_html": "x"}
    a6_swap.append(("points 对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["financial"]["blocks"][0] = "table"
    a6_swap.append(("财务块标量置换", t0))
    for name, t in a6_swap:
        r, _ = run_render(t)
        err = r.stderr or ""
        ok = r.returncode != 0 and "校验失败" in err and "Traceback" not in err
        check("A6 结构破坏干净拒绝：%s" % name, ok, err[-120:])

    t = copy.deepcopy(base_data)
    t["signals"]["key"][0]["sections"][0]["sources"] = t["signals"]["key"][0]["sections"][0]["sources"] + ["E01"]
    r, _ = run_render(t)
    check("A1 编号变形 E01≠E1 干净拒绝", r.returncode != 0 and "E01" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    t["sources"]["items"].append(dict(t["sources"]["items"][0]))
    t["signals"]["dynamic"].append({"id": "dup-test", "text_html": "x", "sources": [t["sources"]["items"][-1]["id"]]})
    r, _ = run_render(t)
    check("A1 重复来源编号干净拒绝", r.returncode != 0 and "重复编号" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    t["signals"]["dynamic"] += [{"id": "d%d" % i, "text_html": "动态%d" % i, "sources": ["E1"]} for i in range(2000)]
    import time
    t_start = time.time()
    r, _ = run_render(t)
    check("A1 规模冒烟（2000 动态项，性能护栏 10s）", r.returncode == 0 and time.time() - t_start < 10, "耗时 %.1fs" % (time.time() - t_start))

    print("\n== FZ 模糊测试首轮回归（M3 fuzz 发现，红队计划 §六同源交付） ==")
    fz_cases = []
    t0 = copy.deepcopy(base_data); t0["overview"]["financial"]["blocks"][0]["type"] = ["table"]
    fz_cases.append(("财务块 type 数组置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["financial"]["blocks"][0]["type"] = {"t": 1}
    fz_cases.append(("财务块 type 对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["mechanisms"]["items"][0]["rows"][0]["sources"] = [["E1"]]
    fz_cases.append(("引用源编号嵌套数组置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["business"]["moat"][0]["sources"] = {"e": "E1"}
    fz_cases.append(("引用源编号对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["signals"]["dynamic"] = 3.14
    fz_cases.append(("signals.dynamic 数值置换", t0))
    t0 = copy.deepcopy(base_data); t0["signals"]["key"] = {"id": "sig1"}
    fz_cases.append(("signals.key 对象置换", t0))
    t0 = copy.deepcopy(base_data); t0["mechanisms"]["items"] = 42
    fz_cases.append(("mechanisms.items 数值置换", t0))
    t0 = copy.deepcopy(base_data); t0["directions"]["items"] = True
    fz_cases.append(("directions.items 布尔置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["business"]["outline_items"] = 1.5
    fz_cases.append(("business.outline_items 数值置换", t0))
    # FZ2：第二轮/三轮 fuzz 发现（79→23→0 过程中转化），同一断言标准。
    # 块类型相关用例统一用锦浪基座（含 table/chart_bar 全类型）；缺锦浪时退化为 base_data
    _jinlang = next((f for f in files if "锦浪" in f.name), None)
    fz_base = json.loads(_jinlang.read_text(encoding="utf-8")) if _jinlang else base_data
    def find_block(t, btype):
        for b in t["overview"]["financial"]["blocks"]:
            if b["type"] == btype:
                return b
        return None
    t0 = copy.deepcopy(base_data); t0["directions"]["items"][1]["state"] = {"s": 1}
    fz_cases.append(("directions.state 对象置换（校验 in 判重 unhashable）", t0))
    t0 = copy.deepcopy(base_data); t0["directions"]["items"][1]["state"] = "s9"
    fz_cases.append(("directions.state 非法枚举值", t0))
    t0 = copy.deepcopy(base_data); t0["sources"]["items"][5]["url_display"] = 42
    fz_cases.append(("sources.url_display 数值置换", t0))
    t0 = copy.deepcopy(base_data); t0["sources"]["items"][5]["url"] = True
    fz_cases.append(("sources.url 布尔置换", t0))
    t0 = copy.deepcopy(base_data); t0["sources"]["legend"] = 7
    fz_cases.append(("sources.legend 数值置换", t0))
    t0 = copy.deepcopy(base_data)
    t0["sources"]["items"][0].pop("url2_display", None)  # 基线可能已带双链接，先摘除再测缺配
    t0["sources"]["items"][0]["url2"] = "https://e.example/x"
    fz_cases.append(("sources.url2 缺 url2_display", t0))
    t0 = copy.deepcopy(fz_base)
    _tb = find_block(t0, "table")
    if _tb and isinstance(_tb.get("rows"), list) and len(_tb["rows"]) > 1:
        _tb["rows"][1] = 5
        fz_cases.append(("table.rows 元素标量置换", t0))
    t0 = copy.deepcopy(fz_base)
    _cb = find_block(t0, "chart_bar")
    if _cb and isinstance(_cb.get("series"), list) and _cb["series"]:
        _cb["series"][0]["name"] = ["n"]
        fz_cases.append(("chart_bar series.name 数组置换", t0))
        t0 = copy.deepcopy(fz_base)
        find_block(t0, "chart_bar")["series"][0]["color"] = "pwned"
        fz_cases.append(("chart_bar series.color 非法值", t0))
    t0 = copy.deepcopy(fz_base)
    _tb2 = find_block(t0, "table")
    if _tb2 is not None:
        _tb2["caption"] = True
        fz_cases.append(("财务块 caption 布尔置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["basic_info"][6]["label"] = {"x": 1}
    fz_cases.append(("basic_info.label 对象置换（set 判重 unhashable）", t0))
    t0 = copy.deepcopy(base_data); t0["signals"]["key"][1]["id"] = 'sig2" onmouseover="x'
    fz_cases.append(("导航 id 含引号（属性位脏污）", t0))
    t0 = copy.deepcopy(fz_base)
    _note_host_found = False
    for b in t0["overview"]["financial"]["blocks"]:
        if b["type"] == "table" and b.get("note"):
            del b["note"]
            b["note_sources"] = ["E1"]
            _note_host_found = True
            break
    if _note_host_found:
        fz_cases.append(("table 有 note_sources 但缺 note（P3 产物层闭环破坏）", t0))
    for name, t in fz_cases:
        r, _ = run_render(t)
        err = r.stderr or ""
        ok = r.returncode != 0 and "校验失败" in err and "Traceback" not in err
        check("FZ 类型破坏干净拒绝：%s" % name, ok, err[-160:])

    # ---- 红队 M4（计划 v0.1 已批准）：A2 编码 Unicode · A8 令牌撞模板 ----
    uni = "“弯引”｜ＡＢＣ‮尾​隐😀𠀀e\u0301"
    t = copy.deepcopy(base_data); t["overview"]["lead"] = uni
    r, html = run_render(t)
    check("A2 Unicode 全量探针直通（弯引号/全角/BIDI/零宽/emoji/CJK-Ext-B/组合符）",
          r.returncode == 0 and uni in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data); t["signals"]["key"][0]["nav"] = "sig\u200b1"
    r, html = run_render(t)
    # 判定锁定（计划 v0.1 A2，P1）：导航显示名为中文文案通道（esc/esc_attr），
    # 零宽/BIDI 字符不致崩不注入（id 通道才收窄字符集），原样留产物即合规
    check("A2 导航含零宽字符不崩不注入（P1 行为锁定）", r.returncode == 0 and "sig\u200b1" in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data); t["meta"]["company_short"] = "超长" * 100
    r, html = run_render(t)
    m = re.search(r'logo-badge[^>]*style="font-size:(\d+)px', html)
    check("A2 超长 company_short 不崩且缩字号收底下限", r.returncode == 0 and m and int(m.group(1)) == 9, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    add_chart(t, ["😀年", "𠀀年"], [{"name": "序列😀", "values": [1, 2]}], caption="图8｜Unicode 测试")
    r, html = run_render(t)
    check("A2 emoji/CJK-Ext-B 入图（SVG 文本转义直通）", r.returncode == 0 and "😀年" in html and "序列😀" in html, (r.stderr or "")[-120:])

    tokens = "{{BODY}} {{COMPANY_NAME}} {{SHORT}} {{SIDENAV}} {{ANCHOR_DATE}} {{SEARCH_HINT}} {{SAMPLE_VERSION}}"
    t = rich_probe(copy.deepcopy(base_data), tokens)
    r, html = run_render(t)
    tok_missing = [tok for tok in tokens.split() if tok not in html]
    check("A8 数据令牌字面量留产物（七令牌全扫描）", r.returncode == 0 and not tok_missing,
          "被吞：%s" % "、".join(tok_missing))

    t = copy.deepcopy(base_data); t["meta"]["company_name"] = "甲{{SHORT}}乙"
    r, html = run_render(t)
    check("A8 meta 撞令牌不交叉替换（company_name 含 {{SHORT}}）",
          r.returncode == 0 and "甲{{SHORT}}乙" in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data); t["meta"]["anchor_date"] = "2026-01-01{{COMPANY_NAME}}"
    r, html = run_render(t)
    check("A8 meta 撞令牌不交叉替换（anchor_date 含 {{COMPANY_NAME}}）",
          r.returncode == 0 and "2026-01-01{{COMPANY_NAME}}" in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data); t["meta"]["company_short"] = "{{BODY}}"
    r, html = run_render(t)
    check("A8 短名撞 {{BODY}} 不串入正文/文件名", r.returncode == 0 and "企业研究_{{BODY}}_" in html, (r.stderr or "")[-120:])

    # ---- 第四轮外部审计新发现（G 系列，2026-10-23，验证为真，同源交付）----
    g_cases = []
    t0 = copy.deepcopy(base_data); t0["overview"]["business"]["heading"] = 3.14
    g_cases.append(("heading 数值置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["business"]["heading"] = "不是对象"
    g_cases.append(("heading 字符串置换", t0))
    t0 = copy.deepcopy(base_data); t0["overview"]["business"]["heading"] = ["a"]
    g_cases.append(("heading 数组置换", t0))
    for name, t in g_cases:
        r, _ = run_render(t)
        err = r.stderr or ""
        ok = r.returncode != 0 and "校验失败" in err and "Traceback" not in err
        check("G8 heading 类型破坏干净拒绝：%s" % name, ok, err[-160:])

    t = copy.deepcopy(base_data); t["meta"]["company_short"] = "词\x00G5TOK0\x00元"
    r, _ = run_render(t)
    check("G1 数据含 sentinel 字面量干净拒绝（防徽章污染）",
          r.returncode != 0 and "校验失败" in (r.stderr or "") and "Traceback" not in (r.stderr or ""), (r.stderr or "")[-120:])

    # G3：骨架文案改版致 precise 锚点失配——必须干净报错，不得静默退化为 HTML 语境替换
    mod_skel = SKEL.read_text(encoding="utf-8").replace("企业研究_{{SHORT}}_", "改版文案_{{SHORT}}_")
    with tempfile.TemporaryDirectory() as td:
        sp = pathlib.Path(td) / "skel.html"
        jp = pathlib.Path(td) / "in.json"
        hp = pathlib.Path(td) / "out.html"
        sp.write_text(mod_skel, encoding="utf-8")
        t = copy.deepcopy(base_data); t["meta"]["company_short"] = 'x";PWNED(1);//'
        jp.write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(RENDER), str(jp), str(sp), str(hp)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        err = r.stderr or ""
        check("G3 骨架锚点缺失 fail-fast（skew 干净报错，不出半成品）",
              r.returncode != 0 and "骨架" in err and "Traceback" not in err and not hp.exists(), err[-160:])

    print("\n== 结构自检（完整渲染） ==")
    r, html = run_render(base_data)
    check("完整渲染成功", r.returncode == 0, (r.stderr or "")[-120:])
    if r.returncode == 0:
        check("无遗留 {{ 令牌（D-82 回归：JS 内 {{SHORT}} 曾漏替）", "{{" not in html)
        check("五模块齐全", all(f'id="p{i}"' in html for i in range(1, 6)))
        check("含 [E#] 来源标记", 'class="src"' in html)
        check("侧边导航非空", html.count('class="sub"') >= 3)
        check("导出按钮齐全", html.count("export-btn") >= 6)
        # ---- A10：等价比对盲区，独立断言兜底 ----
        nav_hrefs = set(re.findall(r'<a class="(?:grp|sub)" href="#([^"]+)"', html))
        miss_tgt = [h for h in nav_hrefs if f'id="{h}"' not in html]
        check("A10 边栏锚点闭环（每个 href 有目标 id）", not miss_tgt, str(miss_tgt)[:120])
        sup_refs = set(re.findall(r'<sup class="src" data-e="(E\d+)"', html))
        miss_row = [e for e in sup_refs if f'id="{e}"' not in html]
        check("A10 [E#]→来源表行闭环（产物层 P3）", not miss_row, str(miss_row)[:120])
        page_names = ["1.0企业概览", "2.0经营事件与信号", "3.0业务及技术解析", "4.0IT关注方向及跟进", "5.0来源索引与证据链"]
        miss_btn = [n for n in page_names if f'data-name="{n}"' not in html]
        check("A10 导出按钮 data-name 与五页标题一致", not miss_btn, str(miss_btn)[:120])

    print("\n== Markdown 导出（N10，需 node；无 node 自动跳过） ==")
    import shutil
    node = shutil.which("node")
    if node and r.returncode == 0:
        js = r"""
const fs=require("fs");
const skel=fs.readFileSync(process.argv[2],"utf8");
const m=skel.match(/function inline\(el[\s\S]*?\r?\n  \}\r?\n  function download\(/);
if(!m){console.error("NO_MATCH");process.exit(2);}
var src=m[0].replace(/\r?\n  \}\r?\n  function download\($/,"\n  }");
function C(x){return {nodeType:3,nodeValue:x};}
function cell(x){return {childNodes:[C(x)],children:[]};}
function row(cs){return {children:cs,querySelectorAll:function(){return [];}};}
var tbl={querySelectorAll:function(){return [row([cell("项目"),cell("数值")]),row([cell("a|b"),cell("c")])];}};
var F=(new Function(src+";return {inline:inline,tableToMd:tableToMd,timelineToMd:timelineToMd,sectionToMd:sectionToMd};"))();
var md=F.tableToMd(tbl);
if(md.indexOf("a\\|b")<0 || (md.match(/\|/g)||[]).length!==10){console.error("BAD_MD:\n"+md);process.exit(1);}
function ok(cond,msg){ if(!cond){console.error("FAIL:"+msg);process.exit(1);} }
// ---- A9 红队 M4：畸形 DOM 桩对抗（不抛裸错）----
ok(F.inline({tagName:"B"})==="", "inline: 无 childNodes 桩");
var circ={tagName:"DIV",childNodes:[]};
circ.childNodes.push({nodeType:1,tagName:"B",childNodes:[circ]});
try{ F.inline(circ); }catch(e){ ok(false,"inline: 循环引用桩抛出裸错 "+e.message); }
ok(F.tableToMd({})==="", "tableToMd: 无 querySelectorAll 桩");
try{ F.tableToMd({querySelectorAll:function(){return [{}];}}); }catch(e){ ok(false,"tableToMd: 行无 children 桩抛出裸错 "+e.message); }
try{ ok(typeof F.timelineToMd({})==="string", "timelineToMd: 空桩"); }catch(e){ ok(false,"timelineToMd: 空桩抛出裸错 "+e.message); }
var svgStr={nodeType:1,tagName:"P",className:{baseVal:"basis"},childNodes:[C("x")]};
ok(F.inline(svgStr)==="x", "inline: SVGAnimatedString 类桩");
var weirdSec={children:[{nodeType:1,tagName:"P",childNodes:[C("hi")]}]};
ok(F.sectionToMd(weirdSec).indexOf("hi")>=0, "sectionToMd: 畸形子节点桩不崩且正常路径不回归");
console.log("MD_OK");
"""
        with tempfile.TemporaryDirectory() as td:
            jp = pathlib.Path(td) / "md_test.js"
            jp.write_text(js, encoding="utf-8")
            rn = subprocess.run([node, str(jp), str(SKEL)], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        check("表格管道符转义生效", rn.returncode == 0 and "MD_OK" in rn.stdout, (rn.stderr or "")[-160:])
    else:
        print("  - 跳过（未找到 node 或无渲染产物）")

    print("\n== 发布纪律（schema 合法性与多副本一致性，D-71/D-80 回归） ==")
    cands = [("仓库", ROOT.parent / "data-contract" / "report-data.schema.json")]
    ws = ROOT
    for _ in range(5):
        ws = ws.parent
        if (ws / "企业研究Skill_进度看板.md").is_file():
            cands += [("工作区根目录", ws / "report-data.schema.json"),
                      ("发布暂存", ws / "_发布_GitHub_v2.0" / "data-contract" / "report-data.schema.json"),
                      ("仓库克隆", ws / "_build" / "github-v2" / "data-contract" / "report-data.schema.json")]
            break
    copies = [(l, p) for l, p in cands if p.is_file()]
    json_ok, json_err = None, ""
    for l, p in copies:
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            json_ok, json_err = False, "%s: %s" % (l, str(e)[:100])
            break
    else:
        json_ok = bool(copies)
    check("schema 合法 JSON（D-71 回归）", json_ok, json_err or "未找到任何 schema 副本")

    dup_ok, dup_err = True, ""
    def no_dup(pairs):
        seen = {}
        for k, v in pairs:
            if k in seen:
                raise ValueError("重复键: " + k)
            seen[k] = v
        return seen
    for l, p in copies:
        try:
            json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=no_dup)
        except ValueError as e:
            dup_ok, dup_err = False, "%s: %s" % (l, str(e)[:100])
            break
    check("schema 无重复键（F13 回归：重复键后者生效会静默吞约束）", dup_ok, dup_err)
    uniq = {p.resolve(): l for l, p in copies}
    if len(uniq) >= 2:
        payloads = {p.read_bytes() for p in uniq}
        check("schema 多副本一致（%s）" % "、".join(uniq.values()),
              len(payloads) == 1,
              "副本内容不一致——按《版本管理规范 v0.2》§三.6，推送前必须 diff 对齐（反面教材：v2.0.4 schema 漏推）")
    else:
        print("  - 多副本一致性跳过（仅单副本，外部独立运行环境）")

    baselines = find_baselines(sys.argv[1:])
    if baselines and len(baselines) == len(files):
        print("\n== 等价比对回归 ==")
        for ex, bl in zip(files, baselines):
            with tempfile.TemporaryDirectory() as td:
                out = pathlib.Path(td) / "r.html"
                r1 = subprocess.run([sys.executable, str(RENDER), str(ex), str(SKEL), str(out)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
                r2 = subprocess.run([sys.executable, str(ROOT / "compare.py"), str(out), str(bl)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
                ok = r1.returncode == 0 and r2.returncode == 0 and "通过" in (r2.stdout or "")
                check(f"等价比对 {ex.name} vs {bl.name}", ok, (r2.stdout or "")[-160:])
    else:
        print("\n== 等价比对回归：跳过（未提供基线样张，或未找到数据实例一一对应） ==")

    fails = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n结论：{'全部通过（%d 项）' % len(RESULTS) if not fails else '失败 %d 项：%s' % (len(fails), '、'.join(fails))}")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
