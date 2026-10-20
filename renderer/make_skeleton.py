# -*- coding: utf-8 -*-
"""从鸣石 v0.8 提取冻结骨架，替换公司特定内容为令牌，生成 skeleton.html"""
import re, pathlib

src = pathlib.Path("企业研究Skill_G3样张_上海鸣石销售成品_v0.8.html").read_text(encoding="utf-8")

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
