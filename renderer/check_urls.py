# -*- coding: utf-8 -*-
"""
来源 URL 可达性检查（D-57 交付前检查单配套工具，零第三方依赖）
用法: python check_urls.py <report.json> [--timeout 12]
说明:
 - HEAD/GET 探测 sources.items[].url/url2，输出 编号/状态/URL 清单；
 - 403/202/超时 不必然等于死链（反爬/JS 渲染页浏览器可开），需人工复核；
 - 建议作为交付前检查单最后一道工序：先 test_renderer.py，再本脚本。
"""
import json, re, sys, ssl, argparse, urllib.request, concurrent.futures as cf

def probe(eid, url, timeout, ctx):
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return eid, url, r.status
    except urllib.error.HTTPError as e:
        return eid, url, e.code
    except Exception:
        return eid, url, "FAIL"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    ap.add_argument("--timeout", type=int, default=12)
    args = ap.parse_args()
    d = json.load(open(args.report_json, encoding="utf-8"))
    refs = [(it["id"], it[k]) for it in d["sources"]["items"] for k in ("url", "url2") if it.get(k)]
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    results = list(cf.ThreadPoolExecutor(8).map(lambda t: probe(*t, args.timeout, ctx),
                                               [(e, u) for e, u in refs]))
    ok = warn = bad = 0
    for eid, url, st in results:
        flag = "✓" if st == 200 else ("⚠" if st in (403, 202, 301, 302) else "✗")
        if st == 200: ok += 1
        elif st in (403, 202, 301, 302): warn += 1
        else: bad += 1
        print(f"  {flag} {eid}  [{st}]  {url}")
    print(f"\n结论：{ok} 直通 / {warn} 需人工复核（反爬或JS页，浏览器尝试打开）/ {bad} 失败")
    sys.exit(0 if bad == 0 else 1)

if __name__ == "__main__":
    main()
