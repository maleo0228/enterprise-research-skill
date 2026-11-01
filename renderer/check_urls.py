# -*- coding: utf-8 -*-
"""
来源 URL 可达性检查（D-57 交付前检查单配套工具，零第三方依赖）
用法: python check_urls.py <report.json> [--timeout 12] [--insecure] [--json]
说明:
 - GET 探测 sources.items[].url/url2，输出 编号/状态/URL/原因 清单；
 - 默认校验 TLS 证书；证书异常单列为 SSL（--insecure 关闭校验，仅作对照）；
 - 跟随重定向，但最终地址与原 URL 不同（跨域或落到首页）时标 ⚠ REDIRECT 供人工复核；
 - 失败细分：DNS／TIMEOUT／REFUSED／SSL-CERT（证书问题）／TLS-EOF（握手被中断，多为代理或出口网络）／NET；http:// 失败时自动用
   https:// 复试一次，以区分"链接失效"与"所在网络禁止明文 http"等环境限制；
 - 403/202/超时/重定向 不必然等于死链（反爬/JS 渲染页浏览器可开），需人工复核；
 - 状态标记为 ASCII（OK/WARN/FAIL），GBK 控制台与重定向输出均可运行。
"""
import json, sys, ssl, socket, argparse, urllib.request, urllib.error, urllib.parse
import concurrent.futures as cf

WARN_CODES = (403, 202, 401, 429)

def _reason(e):
    r = getattr(e, "reason", e)
    if isinstance(r, socket.timeout) or isinstance(e, socket.timeout) or "timed out" in str(r):
        return "TIMEOUT"
    if isinstance(r, ssl.SSLCertVerificationError) or isinstance(e, ssl.SSLCertVerificationError):
        return "SSL-CERT"          # 证书无效/过期/域名不符：链接本身的问题
    if isinstance(r, ssl.SSLError) or isinstance(e, ssl.SSLError):
        return "TLS-EOF"           # 握手被中断：常见于代理/防火墙/出口网络，不必然是死链
    if isinstance(r, socket.gaierror):
        return "DNS"
    if isinstance(r, ConnectionRefusedError):
        return "REFUSED"
    return "NET"

UA = "Mozilla/5.0"

def fetch(url, timeout, ctx):
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.geturl(), ""
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:  # noqa: BLE001 — 网络层异常全部归类，不裸崩
        return "FAIL", url, _reason(e)

def probe(eid, url, timeout, ctx):
    st, final, why = fetch(url, timeout, ctx)
    note = why
    if st != 200 and url.lower().startswith("http://"):
        alt = "https://" + url[7:]
        st2, final2, why2 = fetch(alt, timeout, ctx)
        note = (note or str(st)) + f"；https 复试={st2}{('/' + why2) if why2 else ''}"
        if st2 == 200:
            note += "（http 不可达但 https 可达：多为网络环境禁止明文 http，建议改用 https 链接）"
    redirected = st == 200 and final.rstrip("/") != url.rstrip("/")
    if redirected:
        a, b = urllib.parse.urlsplit(url), urllib.parse.urlsplit(final)
        if a.netloc != b.netloc or (b.path in ("", "/") and a.path not in ("", "/")):
            note = f"重定向至 {final}"
        else:
            redirected = False
    return {"id": eid, "url": url, "status": st, "final_url": final, "reason": note, "redirect": redirected}

def classify(r):
    if r["status"] == 200 and not r["redirect"]:
        return "OK"
    if r["status"] == 200 or r["status"] in WARN_CODES or r["reason"] in ("TIMEOUT", "TLS-EOF") or "https 复试=200" in r["reason"]:
        return "WARN"
    return "FAIL"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_json")
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--insecure", action="store_true", help="关闭 TLS 证书校验（仅作对照）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    ap.add_argument("--user-agent", default=None,
                    help="自定义 User-Agent（如 SEC EDGAR 要求 \"Name email@example.com\"，默认 UA 返回 403）")
    args = ap.parse_args()
    global UA
    if args.user_agent:
        UA = args.user_agent
    d = json.load(open(args.report_json, encoding="utf-8"))
    refs = [(it["id"], it[k]) for it in d["sources"]["items"] for k in ("url", "url2") if it.get(k)]
    ctx = ssl.create_default_context()
    if args.insecure:
        ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(lambda t: probe(*t, args.timeout, ctx), refs))
    cnt = {"OK": 0, "WARN": 0, "FAIL": 0}
    for r in results:
        r["verdict"] = classify(r); cnt[r["verdict"]] += 1
    if args.json:
        print(json.dumps({"results": results, "summary": cnt}, ensure_ascii=False, indent=1))
    else:
        for r in results:
            extra = f"  -- {r['reason']}" if r["reason"] else ""
            print(f"  {r['verdict']:<4} {r['id']}  [{r['status']}]  {r['url']}{extra}")
        print(f"\n结论：{cnt['OK']} 直通 / {cnt['WARN']} 需人工复核（反爬、JS 页、重定向或网络环境限制）/ {cnt['FAIL']} 失败")
    sys.exit(0 if cnt["FAIL"] == 0 else 1)

if __name__ == "__main__":
    main()
