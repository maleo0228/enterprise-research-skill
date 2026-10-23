
// 开发辅助脚本：node _dbg_md_test.js <skeleton.html>
// 第四轮审计 F10 附带修复：① argv 差一（原读 argv[1]=脚本自身，应为 argv[2]=骨架）；
// ② 提取正则未随 inline(el, depth) 签名更新（A9 加固后旧正则 NO_MATCH）
const fs=require("fs");
const skel=fs.readFileSync(process.argv[2],"utf8");
const m=skel.match(/function inline\(el[\s\S]*?\r?\n  \}\r?\n  function cardToMd/);
if(!m){console.error("NO_MATCH");process.exit(2);}
var src=m[0].replace(/\r?\n  \}\r?\n  function cardToMd/,"\n  }");
var tableToMd=(new Function(src+";return tableToMd;"))();
function C(x){return {nodeType:3,nodeValue:x};}
function cell(x){return {childNodes:[C(x)],children:[]};}
function row(cs){return {children:cs,querySelectorAll:function(){return [];}};}
var tbl={querySelectorAll:function(){return [row([cell("项目"),cell("数值")]),row([cell("a|b"),cell("c")])];}};
var md=tableToMd(tbl);
if(md.indexOf("a\\|b")>=0 && (md.match(/\|/g)||[]).length===10){console.log("MD_OK");}
else{console.error("BAD_MD:\n"+md);process.exit(1);}
