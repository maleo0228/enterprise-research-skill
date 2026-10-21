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

    t = copy.deepcopy(base_data)
    for b in t["overview"]["financial"]["blocks"]:
        if b.get("type") == "chart_bar":
            for s in b["series"]:
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
    for b in t["overview"]["financial"]["blocks"]:
        if b.get("type") == "chart_bar":
            b["series"][0]["values"] = b["series"][0]["values"][:-1]
    r, _ = run_render(t)
    check("M2 序列长度不一致拒绝", r.returncode != 0 and "长度" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    for b in t["overview"]["financial"]["blocks"]:
        if b.get("type") == "chart_bar":
            b["categories"] = []
    r, _ = run_render(t)
    check("M2 categories 为空拒绝", r.returncode != 0 and "categories" in (r.stderr or ""), (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    for b in t["overview"]["financial"]["blocks"]:
        if b.get("type") == "chart_bar":
            b["series"][0]["values"] = ["abc"] * len(b["categories"])
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

    print("\n== 结构自检（完整渲染） ==")
    r, html = run_render(base_data)
    check("完整渲染成功", r.returncode == 0, (r.stderr or "")[-120:])
    if r.returncode == 0:
        check("五模块齐全", all(f'id="p{i}"' in html for i in range(1, 6)))
        check("含 [E#] 来源标记", 'class="src"' in html)
        check("侧边导航非空", html.count('class="sub"') >= 3)
        check("导出按钮齐全", html.count("export-btn") >= 6)

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
