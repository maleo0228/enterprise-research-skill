# -*- coding: utf-8 -*-
"""
G5 body 等价比对：渲染输出 vs 基线样张
口径（D-66/D-67 定义）：
 1. 文本逐字一致：剥离全部 <sup> 后，空白（含换行/缩进）归一，按页（p1–p5）比较；
 2. 来源引用按集合比对：每页内 data-e 值折叠为集合，与基线集合相等（JSON 侧去重、基线重复引用折叠）；
 3. SVG 坐标允许差异：只比对 aria-label 与图内文本（图例/类目/数值），不比对坐标；
 4. 已登记归一化：鸣石基线业务 h3 内联 style、缺失的时间线命名行（渲染侧补"图N｜"）、
    命名行 margin-top 统一 14px（基线 12/16px）、sup 附着位置（段落末 vs 句中）。
用法: python compare.py <渲染.html> <基线.html>
"""
import re, sys, html, difflib, pathlib

# 已登记基线修复（D-68：锦浪 v0.2 遗留过程用语，渲染版按《页面呈现规范》元语言禁令修正；
# 比对前对基线套用同一修正，使比对聚焦结构等价；清单逐条可审）
REGISTERED_FIXES = [
    ("时点与金额均明确（第一层来源），", "时点与金额均明确（募集说明书与年报等一手资料），"),
    ("研发中心（第一层来源，建设期至约 2027）", "研发中心（建设期至约 2027）"),
    ("研发中心募投均为第一层来源。", "研发中心募投均见年报与募集说明书。"),
    ("智能仓储/搬运/检测均为第一层来源。", "智能仓储/搬运/检测均见年报与募集说明书。"),
    ("海外收入占比为第一层来源。", "海外收入占比见年报披露。"),
    ("锦浪云平台功能为官网/年报第一层来源。", "锦浪云平台功能为官网与年报明确披露。"),
    ("电站规模为年报第一层来源。", "电站规模见年报披露。"),
    ("2026Q2 收入为半年报第一层来源；", "2026Q2 收入见半年报；"),
    ("年报自述（第一层来源），全部方向中证据最硬", "年报自述（一手披露），全部方向中证据最硬"),
    ("研发中心募投 2.48 亿（第一层）＋", "研发中心募投 2.48 亿（一手披露）＋"),
    ("平台存在为事实（官网/年报第一层）；", "平台存在为事实（官网/年报明确披露）；"),
    ("业务放量为公司交流口径（第二层为主）＋2026Q2 收入为半年报第一层；",
     "业务放量为公司交流口径（媒体与交流会口径为主）＋2026Q2 收入见半年报；"),
    ("政策为第二层、敞口数据为第一层；", "政策为媒体报道、敞口数据为年报披露；"),
    ("依据：年报第一层；但资产在轻资产化收缩转出", "依据：年报披露；但资产在轻资产化收缩转出"),
    ("第一层（经层2工具转述）", "企业事实（经聚合工具转述）"),
    ("第一层（经聚合页转述，年报原文已核 E3）", "企业事实（经聚合页转述，年报原文已核 E3）"),
]

def sections(t):
    """按页切分 {pid: 页面片段}"""
    out = {}
    for m in re.finditer(r'<section class="page" id="(p\d)">(.*?)(?=<section class="page" id="p\d">|</div>\s*\r?\n\r?\n<footer>)', t, re.S):
        out[m.group(1)] = m.group(2)
    return out

def norm_text(frag):
    """归一化后与基线做文本逐字比较：
    1) 剥离 <sup>（来源引用按集合另比）；2) 去 HTML 注释（节间注释不渲染）；
    3) 弯直引号归一（G3 基线为半角直引号，实例为全角弯引号，视觉等价）；
    4) SVG 整体换令牌（坐标/元素顺序不逐字比，文本经 svg_texts 另比）；
    5) 命名行 margin-top 归一为 14px（基线 12/16px 手调差异）；
    6) 时间线前命名行忽略（鸣石 v0.8 缺命名行系基线缺陷，渲染侧按规范补齐，已登记归一化）；
    7) 压缩全部空白。"""
    frag = re.sub(r'<sup[^>]*>.*?</sup>', '', frag, flags=re.S)
    frag = re.sub(r'<!--.*?-->', '', frag, flags=re.S)
    frag = frag.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    frag = re.sub(r'<svg.*?</svg>', '⟦SVG⟧', frag, flags=re.S)
    frag = frag.replace('margin-top:12px', 'margin-top:14px').replace('margin-top:16px', 'margin-top:14px')
    frag = frag.replace(' style="margin-top:20px"', '')
    frag = re.sub(r'<p style="margin-top:14px"><b>图\d+｜[^<]*</b></p>(?=\s*<div class="timeline">)',
                  '', frag)
    frag = re.sub(r'\s+', '', frag)
    return frag

def sup_set(frag):
    return set(re.findall(r'<sup class="src" data-e="(E\d+)">', frag))

def svg_texts(frag):
    """提取 svg 的 aria-label 与全部文本节点文字（排序后比较，元素顺序不敏感）"""
    out = []
    for m in re.finditer(r'<svg[^>]*aria-label="([^"]*)"[^>]*>(.*?)</svg>', frag, re.S):
        out.append((html.unescape(m.group(1)),
                    sorted(re.sub(r'\s+', '', t) for t in re.findall(r'<text[^>]*>([^<]*)</text>', m.group(2)))))
    return out

def main():
    a = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    b = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
    applied = 0
    for old, new in REGISTERED_FIXES:
        if old in b:
            b = b.replace(old, new)
            applied += 1
    if applied:
        print(f"已对基线套用已登记修复 {applied} 处（过程用语去元语言化，见 REGISTERED_FIXES）")
    sa, sb = sections(a), sections(b)
    ok = True
    for pid in ["p1", "p2", "p3", "p4", "p5"]:
        fa, fb = sa.get(pid, ""), sb.get(pid, "")
        if not fa or not fb:
            print(f"[{pid}] 缺失：渲染={'有' if fa else '无'} 基线={'有' if fb else '无'}")
            ok = False
            continue
        ta, tb = norm_text(fa), norm_text(fb)
        if ta == tb:
            print(f"[{pid}] 文本逐字一致 ✓")
        else:
            ok = False
            print(f"[{pid}] 文本差异 ✗（渲染 {len(ta)} 字符 / 基线 {len(tb)} 字符）")
            sm = difflib.SequenceMatcher(None, tb, ta)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != "equal":
                    print(f"    {tag}: 基线[{tb[max(0,i1-20):i2+20]}]")
                    print(f"          渲染[{ta[max(0,j1-20):j2+20]}]")
        ua, ub = sup_set(fa), sup_set(fb)
        if ua == ub:
            print(f"[{pid}] 来源集合一致 ✓（{len(ua)} 条）")
        else:
            ok = False
            print(f"[{pid}] 来源集合差异 ✗ 仅基线有 {sorted(ub-ua)} 仅渲染有 {sorted(ua-ub)}")
        va, vb = svg_texts(fa), svg_texts(fb)
        if [x[0] for x in va] == [x[0] for x in vb] and [x[1] for x in va] == [x[1] for x in vb]:
            if va:
                print(f"[{pid}] SVG 文本一致 ✓（{len(va)} 幅）")
        else:
            ok = False
            print(f"[{pid}] SVG 差异 ✗ 渲染={va} 基线={vb}")
    # 页外：title / footer / 边栏
    for label, pat in [("title", r"<title>(.*?)</title>"),
                       ("footer", r"<footer>(.*?)</footer>"),
                       ("logo名", r'<div class="logo-name">(.*?)</div>'),
                       ("logo副", r'<div class="logo-sub">(.*?)</div>')]:
        ma, mb = re.search(pat, a, re.S), re.search(pat, b, re.S)
        ca = re.sub(r'\s+', '', ma.group(1)) if ma else ""
        cb = re.sub(r'\s+', '', mb.group(1)) if mb else ""
        if label == "title":  # 版本号随产物递增，比对时归一
            ca = re.sub(r'样张v[\d.]+', '样张', ca)
            cb = re.sub(r'样张v[\d.]+', '样张', cb)
        if ca == cb:
            print(f"[页外] {label} 一致 ✓")
        else:
            ok = False
            print(f"[页外] {label} 差异 ✗ 渲染={ca} 基线={cb}")
    na = len(re.findall(r'<a class="(?:grp|sub)"', a))
    nb = len(re.findall(r'<a class="(?:grp|sub)"', b))
    print(f"[页外] 边栏导航项 渲染 {na} / 基线 {nb} " + ("✓" if na == nb else "✗"))
    if na != nb:
        ok = False
    print("\n结论：" + ("等价比对通过 ✓" if ok else "存在差异 ✗"))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
