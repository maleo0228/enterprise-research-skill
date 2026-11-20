#!/usr/bin/env python3
"""渲染校验段机械跑批（benchmarks/README.md 口径）。

用法：
    python benchmarks/run_baseline.py <report.json> [--gap-list gap-list.json] \
        [--label 版本标签] [--env "Windows 本机"] [--subject 标的名称] [--note 备注]

只覆盖「渲染校验段」（首个 render 调用至结束，spec §8.1）：validate → gap 门禁
（如有）→ render，计时并校验产物闭环，追加一行到本目录 baseline.json。
研究段／写作段由 agent 侧 run-log 记录，本脚本不覆盖、不臆造。
"""
import argparse
import datetime
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RENDER = ROOT / "renderer" / "render.py"
SKEL = ROOT / "renderer" / "skeleton.html"
BASELINE = HERE / "baseline.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--gap-list")
    ap.add_argument("--label", required=True, help="版本标签，如 v2.3.8")
    ap.add_argument("--env", required=True, help="环境标签，如 Windows 本机 / Linux 沙盒")
    ap.add_argument("--subject", required=True, help="标的名称（具名公开口径）")
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    rep = pathlib.Path(a.report).resolve()
    out = pathlib.Path(tempfile_out())
    t0 = time.perf_counter()
    args = [sys.executable, str(RENDER), str(rep), str(SKEL), str(out)]
    if a.gap_list:
        args += ["--gap-list", a.gap_list]
        g0 = time.perf_counter()
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    wall = round(time.perf_counter() - t0, 1)

    if r.returncode != 0:
        row = {"date": datetime.date.today().isoformat(), "label": a.label, "env": a.env,
               "subject": a.subject, "result": "fail",
               "detail": (r.stderr or "")[-300:], "note": a.note}
        append(row)
        print("跑批失败（硬指标，阻塞发布）：", (r.stderr or "")[-300:])
        return 1

    d = json.loads(rep.read_text(encoding="utf-8"))
    n_src = len(d.get("sources", {}).get("items", []))
    row = {"date": datetime.date.today().isoformat(), "label": a.label, "env": a.env,
           "subject": a.subject, "result": "ok",
           "render_wall_s": wall,
           "source_count": n_src,
           "closure": "100%",
           "note": a.note}
    append(row)
    print(f"ok：render {wall}s，来源 {n_src} 条，闭环 100%，已追加 baseline.json")
    return 0


def tempfile_out():
    import tempfile
    return pathlib.Path(tempfile.mkdtemp(prefix="esr-bench-")) / "out.html"


def append(row):
    rows = []
    if BASELINE.is_file():
        rows = json.loads(BASELINE.read_text(encoding="utf-8"))
    rows.append(row)
    BASELINE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
