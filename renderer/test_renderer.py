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
    t["overview"]["basic_info"].append({"label": "注册资本", "value_html": "326.4082 万元", "sources": ["E1"]})
    r, html = run_render(t)
    check("N2 basic_info 追加尽调扩展项", r.returncode == 0 and "326.4082 万元" in html, (r.stderr or "")[-120:])

    t = copy.deepcopy(base_data)
    t["overview"]["basic_info"] = t["overview"]["basic_info"][1:]
    r, _ = run_render(t)
    check("N2 核心 8 项缺项仍拒绝", r.returncode != 0 and "basic_info" in (r.stderr or ""), (r.stderr or "")[-120:])

    print("\n== 结构自检（完整渲染） ==")
    r, html = run_render(base_data)
    check("完整渲染成功", r.returncode == 0, (r.stderr or "")[-120:])
    if r.returncode == 0:
        check("五模块齐全", all(f'id="p{i}"' in html for i in range(1, 6)))
        check("含 [E#] 来源标记", 'class="src"' in html)
        check("侧边导航非空", html.count('class="sub"') >= 3)
        check("导出按钮齐全", html.count("export-btn") >= 6)

    print("\n== Markdown 导出（N10，需 node；无 node 自动跳过） ==")
    import shutil
    node = shutil.which("node")
    if node and r.returncode == 0:
        js = r"""
const fs=require("fs");
const skel=fs.readFileSync(process.argv[2],"utf8");
const m=skel.match(/function inline\(el\)\{[\s\S]*?\r?\n  \}\r?\n  function cardToMd/);
if(!m){console.error("NO_MATCH");process.exit(2);}
var src=m[0].replace(/\r?\n  \}\r?\n  function cardToMd/,"\n  }");
function C(x){return {nodeType:3,nodeValue:x};}
function cell(x){return {childNodes:[C(x)],children:[]};}
function row(cs){return {children:cs,querySelectorAll:function(){return [];}};}
var tbl={querySelectorAll:function(){return [row([cell("项目"),cell("数值")]),row([cell("a|b"),cell("c")])];}};
var md=(new Function(src+";return tableToMd;"))()(tbl);
if(md.indexOf("a\\|b")>=0 && (md.match(/\|/g)||[]).length===10){console.log("MD_OK");}
else{console.error("BAD_MD:\n"+md);process.exit(1);}
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
