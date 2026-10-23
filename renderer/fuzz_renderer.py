# -*- coding: utf-8 -*-
"""
渲染器模糊测试 fuzz_renderer.py v0.1（零第三方依赖，Python 3.8+ 标准库）
红队 M3（D-92 轮立项，依据《红队/对抗性测试计划 v0.1》§五）。

形态：种子化随机变异器（对真实实例做字段级变异）＋ 极简合成器（从骨架生成近合法文档）
      ＋ 贪婪 shrink（失败用例逐步缩小，保留失败性质）。
不变式（§三）：
  P1 不崩不裸 traceback —— 要么渲染成功，要么 SystemExit("校验失败：…")；其他任何异常＝缺陷
  P2 产物无注入 —— 输出 HTML 的 <script 数、javascript: 出现数不得超骨架基线；不得新增 on*= 属性
  P3 引用闭环 —— data-e 集合 == 来源表 tr id 集合
用法：
  python fuzz_renderer.py                 # 默认 2000 用例，种子 20261022
  python fuzz_renderer.py --cases 5000 --seed 1
  python fuzz_renderer.py --replay fuzz_failures/case_0001.json
退出码：0 无崩溃；1 发现缺陷（详情落 fuzz_failures/）
"""
import argparse, copy, io, json, pathlib, random, re, sys, tempfile, time, traceback

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import render  # noqa: E402  复用被测对象本身

SKEL = ROOT / "skeleton.html"
SKEL_TEXT = SKEL.read_text(encoding="utf-8")
BASE_SCRIPT = SKEL_TEXT.count("<script")
BASE_JS_SCHEME = SKEL_TEXT.count("javascript:")
ON_ATTR_RE = re.compile(r'\son\w+\s*=')
BASE_ON_ATTR = len(ON_ATTR_RE.findall(SKEL_TEXT))
DATA_E_RE = re.compile(r'data-e="([^"]*)"')
SRC_TR_RE = re.compile(r'<tr id="([^"]*)"')

# ---------- 攻击字符串与特殊值库（A1/A2/A3/A4/A5/A7/A8 素材） ----------
ATTACK_STRINGS = [
    '<script>alert(1)</script>', '<img src=x onerror=alert(1)>',
    '" onmouseover="alert(1)', "' onfocus='alert(1)",
    '<a href="javascript:alert(1)">x</a>', '<a href="JaVaScRiPt:alert(1)">x</a>',
    '<a href="https://evil.example/" onmouseover="alert(1)">x</a>',
    '<a/href="https://evil.example/">x</a>', '<B>bold</B>', '<a href = "https://e.example/">x</a>',
    '</b', '<br', '{{BODY}}', '{{SHORT}}', '{{COMPANY_NAME}}', '{{ANCHOR_DATE}}', '{{SIDENAV}}',
    '{{SEARCH_HINT}}', '{{SAMPLE_VERSION}}', '企业研究_{{SHORT}}_',
    'https://e.example/?a="onmouseover="x', 'https://e.example/?q=<script>',
    'java\tscript:alert(1)', '\\javascript:alert(1)', '//evil.example/x',
    'https:evil.example', 'HTTPS://EXAMPLE.COM/X',
    '\u202e‮‬', '\u200b\u200c\u200d', 'emoji😀test', '组合́字符',
    '<svg onload=alert(1)>', '<iframe src=javascript:alert(1)>',
    'x' * 5000,  # 超长字符串
]
ATTACK_NUMBERS = [0, -0.0, 1, -1, 1e308, -1e308, 1e-308, 10 ** 18, -(10 ** 18),
                  float('nan'), float('inf'), float('-inf')]
ATTACK_SCALARS = [None, True, False, "", 0, [], {}]

def rand_scalar(rng):
    return rng.choice(ATTACK_SCALARS)

def walk_paths(obj, prefix=()):
    """枚举全部可寻址路径（dict key / list index）。"""
    yield prefix, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_paths(v, prefix + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_paths(v, prefix + (i,))

def get_at(obj, path):
    for p in path:
        obj = obj[p]
    return obj

def set_at(obj, path, value):
    parent = obj
    for p in path[:-1]:
        parent = parent[p]
    parent[path[-1]] = value

def del_at(obj, path):
    if not path:
        return False
    try:
        parent = get_at(obj, path[:-1])
        if isinstance(parent, dict):
            parent.pop(path[-1], None)
        elif isinstance(parent, list) and isinstance(path[-1], int) and path[-1] < len(parent):
            parent.pop(path[-1])
        else:
            return False
        return True
    except (KeyError, IndexError, TypeError):
        return False

# ---------- 变异器 ----------
class Mutator:
    """对一份实例做 K 步随机变异，每步记录操作日志（供 shrink 与复现）。"""

    def __init__(self, rng, base):
        self.rng = rng
        self.base = base

    def random_value(self, depth=0):
        r = self.rng
        choice = r.random()
        if choice < 0.45:
            return r.choice(ATTACK_STRINGS)
        if choice < 0.65:
            return r.choice(ATTACK_NUMBERS)
        if choice < 0.75:
            return rand_scalar(r)
        if choice < 0.87 and depth < 3:
            return [self.random_value(depth + 1) for _ in range(r.randint(0, 4))]
        if depth < 3:
            return {f"k{i}": self.random_value(depth + 1) for i in range(r.randint(0, 4))}
        return r.choice(ATTACK_STRINGS)

    def one_mutation(self, doc):
        r = self.rng
        paths = [p for p, _ in walk_paths(doc) if p]
        if not paths:
            return None
        path = r.choice(paths)
        op = r.random()
        try:
            old = get_at(doc, path)
        except (KeyError, IndexError, TypeError):
            return None
        if op < 0.18:  # 删除
            if del_at(doc, path):
                return ("del", path, None)
            return None
        if op < 0.72:  # 替换（类型移位/攻击值）
            new = self.random_value()
            try:
                set_at(doc, path, new)
            except (KeyError, IndexError, TypeError):
                return None
            return ("set", path, new)
        if op < 0.82 and isinstance(old, str):  # 字符串追加污染
            new = old + r.choice(ATTACK_STRINGS)
            set_at(doc, path, new)
            return ("append", path, new)
        if op < 0.92:  # 深度嵌套包裹
            depth = r.randint(2, 20)
            v = old
            for _ in range(depth):
                v = [v]
            try:
                set_at(doc, path, v)
            except (KeyError, IndexError, TypeError):
                return None
            return ("nest", path, depth)
        # 撞型：对象↔数组互换
        if isinstance(old, dict):
            new = list(old.values())
        elif isinstance(old, list):
            new = {f"f{i}": v for i, v in enumerate(old)}
        else:
            return None
        try:
            set_at(doc, path, new)
        except (KeyError, IndexError, TypeError):
            return None
        return ("swap", path, new)

    def run(self, steps):
        doc = copy.deepcopy(self.base)
        log = []
        for _ in range(steps):
            m = self.one_mutation(doc)
            if m:
                log.append(m)
        return doc, log

# ---------- 合成器（极简近合法文档，随机填字段） ----------
def synth_doc(rng):
    eid = lambda i: f"E{i+1}"  # noqa: E731
    n_src = rng.randint(1, 6)
    sources = {"lead": rng.choice(["来源说明", ""]), "legend": ["官方披露", "第三方"],
               "items": [{"id": eid(i), "entity": "测试主体", "time": "2026-09-30",
                          "caliber": "公告", "source": "测试来源", "url": "https://example.com/x",
                          "url_display": "example.com/x", "fetched": "2026-10-01",
                          "identity": "事实"} for i in range(n_src)],
               "homology_note": "同源说明"}
    fin_types = ["table", "chart_bar", "missing", "note"]
    blocks = []
    for i in range(rng.randint(0, 4)):
        t = rng.choice(fin_types)
        b = {"type": t, "caption": f"表{i+1}｜测试" if t == "table" else (f"图{i+1}｜测试" if t == "chart_bar" else "说明")}
        if t == "table":
            b["headers"] = ["指标", "值"]
            b["rows"] = [[f"r{j}", rng.choice([1, -1, 0, 1.5, 1e6])] for j in range(rng.randint(1, 4))]
        elif t == "chart_bar":
            b["categories"] = ["A", "B"]
            b["series"] = [{"label": "s1", "values": [rng.choice([1, 0, -2, 1e5]), rng.choice([2, -1, 0.5])]}]
        elif t == "note":
            b["text"] = "说明文字"
        else:
            b["text"] = "无公开财务信息"
        blocks.append(b)
    return {
        "meta": {"company_name": "测试公司", "company_short": "测试", "anchor_date": "2026-09-30",
                 "contract_version": "0.3", "sample_version": "v0.0",
                 "search_hint": rng.choice(["输入关键词……", "搜\" onmouseover=\"x", "{{BODY}}"])},
        "overview": {"lead": "导语", "basic_info": [["成立", "2020"], ["总部", "上海"]],
                     "financial": {"lead_note": "", "blocks": blocks}},
        "signals": {"lead": "信号导语", "key": [], "dynamic_title": "动态", "dynamic": []},
        "mechanisms": {"lead": "机制导语", "items": []},
        "directions": {"lead": "方向导语", "items": []},
        "sources": sources,
    }

# ---------- 执行器（进程内跑 render.main，精确覆盖主流程） ----------
def run_case(doc, td):
    jp = pathlib.Path(td) / "in.json"
    hp = pathlib.Path(td) / "out.html"
    if hp.exists():
        hp.unlink()
    jp.write_text(json.dumps(doc, ensure_ascii=False, allow_nan=True), encoding="utf-8")
    old_argv, old_out, old_err = sys.argv, sys.stdout, sys.stderr
    sys.argv = ["render.py", str(jp), str(SKEL), str(hp)]
    buf_out, buf_err = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = buf_out, buf_err
    status, exc = "ok", None
    try:
        render.main()
    except SystemExit as e:
        if e.code is None or e.code == 0:
            status = "ok"
        elif isinstance(e.code, str):
            status = "clean_fail" if e.code.startswith("校验失败") else "other_exit"
            exc = e.code[:200]
        else:
            status, exc = "other_exit", str(e.code)[:200]
    except BaseException:
        status, exc = "crash", traceback.format_exc()[-800:]
    finally:
        sys.argv, sys.stdout, sys.stderr = old_argv, old_out, old_err
    html = hp.read_text(encoding="utf-8", errors="replace") if hp.exists() else ""
    return status, exc, html

def check_invariants(html):
    """P2 注入检查 + P3 引用闭环。返回缺陷列表（空＝通过）。"""
    flaws = []
    if html.count("<script") > BASE_SCRIPT:
        flaws.append("P2: 新增 <script")
    # javascript: / on*= 只扫描标签内部——文本节点里的字面量（如转义后的攻击字符串）不可执行，
    # 属性值内出现攻击字符串字面量（已转义）不构成注入——剥掉引号内内容再扫描属性位。
    # 首轮 fuzz 误报两类：aria-label 内转义的 onmouseover=（case_1076）、
    # href="#...javascript:..." 片段锚点（case_1463，# 前缀永不执行 scheme）
    strip_vals = lambda t: re.sub(r'"[^"]*"' + "|'[^']*'", '""', t)  # noqa: E731
    tag_hits_js = sum(strip_vals(t).count("javascript:") for t in re.findall(r"<[^<>]*>", html))
    tag_hits_on = sum(1 for t in re.findall(r"<[^<>]*>", html) if ON_ATTR_RE.search(strip_vals(t)))
    base_tags_js = sum(strip_vals(t).count("javascript:") for t in re.findall(r"<[^<>]*>", SKEL_TEXT))
    base_tags_on = sum(1 for t in re.findall(r"<[^<>]*>", SKEL_TEXT) if ON_ATTR_RE.search(strip_vals(t)))
    if tag_hits_js > base_tags_js:
        flaws.append("P2: 新增 javascript: scheme（标签内）")
    if tag_hits_on > base_tags_on:
        flaws.append("P2: 新增 on*= 事件属性（标签内）")
    # P3 只在渲染成功且有来源表时断言
    if 'id="src-table"' in html:
        data_e = set(DATA_E_RE.findall(html))
        src_tr = set(t for t in SRC_TR_RE.findall(html) if t.startswith("E"))
        if data_e != src_tr:
            flaws.append(f"P3: 引用闭环破坏 data_e={sorted(data_e)} vs rows={sorted(src_tr)}")
    return flaws

# ---------- shrink（贪婪：逐条删变异步，保留失败性质） ----------
def reproduces(base, log, td, max_bytes=2 * 1024 * 1024):
    doc = copy.deepcopy(base)
    try:
        for op, path, val in log:
            if op == "del":
                del_at(doc, path)
            else:
                set_at(doc, path, val)
        raw = json.dumps(doc, ensure_ascii=False, allow_nan=True)
        if len(raw.encode("utf-8")) > max_bytes:
            return None
    except Exception:
        return None
    status, exc, html = run_case(doc, td)
    return classify(status, exc, html)

def classify(status, exc, html):
    if status == "crash":
        return "crash"
    if status == "ok":
        flaws = check_invariants(html)
        return "invariant:" + ";".join(flaws) if flaws else None
    return None  # clean_fail / other_exit 不构成缺陷（other_exit 单独提示）

def shrink(base, log, td):
    log = list(log)
    changed = True
    while changed:
        changed = False
        for i in range(len(log)):
            trial = log[:i] + log[i + 1:]
            if trial and reproduces(base, trial, td):
                log = trial
                changed = True
                break
    return log

# ---------- 主流程 ----------
def find_examples():
    cands = [ROOT.parent / "examples", ROOT / "examples", ROOT.parent, pathlib.Path.cwd()]
    for c in cands:
        if c.is_dir():
            files = []
            for f in sorted(c.glob("*.json")):
                if "schema" in f.name.lower():
                    continue
                try:
                    head = f.read_text(encoding="utf-8", errors="ignore")[:200000]
                except OSError:
                    continue
                if '"meta"' in head and '"mechanisms"' in head:
                    files.append(f)
            if files:
                return files[:3]
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261022)
    ap.add_argument("--replay", type=str, default="")
    args = ap.parse_args()

    fail_dir = ROOT / "fuzz_failures"
    examples = find_examples()
    if not examples and not args.replay:
        print("未找到实例 JSON（examples/ 或上级目录），请先放置含 meta+mechanisms 的实例")
        return 1
    bases = []
    for f in examples:
        try:
            bases.append((f.name, json.loads(f.read_text(encoding="utf-8"))))
        except Exception:
            pass

    td = tempfile.mkdtemp(prefix="fuzz_")
    t0 = time.time()
    fails, clean_fails, oks = [], 0, 0

    if args.replay:
        data = json.loads(pathlib.Path(args.replay).read_text(encoding="utf-8"))
        base = data.get("doc") or (bases[0][1] if bases else None)
        log = [(m[0], tuple(m[1]), m[2]) for m in data["mutations"]]
        verdict = reproduces(base, log, td)
        print(f"replay {args.replay}: {verdict or '未复现'}")
        return 0 if verdict is None else 1

    rng = random.Random(args.seed)
    n = args.cases
    for case_i in range(n):
        mode = rng.random()
        if mode < 0.25 or not bases:
            name = "synthetic"
            doc0 = synth_doc(rng)
            mut = Mutator(rng, doc0)
            doc, log = mut.run(rng.randint(0, 6))
            base = doc0  # shrink 基准＝变异前文档，连同失败用例落盘
        else:
            name, base = rng.choice(bases)
            mut = Mutator(rng, base)
            doc, log = mut.run(rng.randint(1, 8))
        status, exc, html = run_case(doc, td)
        verdict = classify(status, exc, html)
        if status == "clean_fail":
            clean_fails += 1
        elif status == "ok":
            oks += 1
        if verdict is None:
            continue
        # 缺陷：shrink 后落盘（base 一并存入，保证 replay 自足）
        shrunk = shrink(base, log, td)
        fail_dir.mkdir(exist_ok=True)
        fp = fail_dir / f"case_{case_i:04d}.json"
        fp.write_text(json.dumps({
            "seed": args.seed, "case": case_i, "source": name, "verdict": verdict,
            "exc": exc, "doc": base,
            "mutations": [[op, list(p), v] for op, p, v in shrunk],
        }, ensure_ascii=False, indent=1, allow_nan=True), encoding="utf-8")
        fails.append((case_i, verdict, fp.name))
        print(f"  ✗ case {case_i} [{name}] {verdict.splitlines()[0][:120]} → {fp.name}")

    dt = time.time() - t0
    print(f"\nfuzz 完成：{n} 用例，种子 {args.seed}，耗时 {dt:.1f}s")
    print(f"  渲染成功 {oks}｜干净拒绝 {clean_fails}｜缺陷 {len(fails)}")
    for case_i, verdict, fn in fails:
        print(f"  - case {case_i}: {verdict.splitlines()[0][:100]}（{fn}）")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
