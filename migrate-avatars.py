#!/usr/bin/env python3
"""头像依赖迁移：avatar.tgnav.org → 本地文件优先，缺失时用 ui-avatars.com 字母头像。

策略（三层兜底，在原 HTML 的换图链上叠加）：
  1. /avatars/small/{username}.jpg —— 本地真实头像（fetch-avatars.py 抓取后放入）
  2. https://ui-avatars.com/api/?name={首字}&background=random —— 字母头像
  3. /images/default.jpg —— 原有默认图（保留）

用法:  python3 migrate-avatars.py            # 全站替换
       python3 migrate-avatars.py --dry-run  # 仅预览
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DRY = "--dry-run" in sys.argv

# 原 onload 换图链（跨行属性值）与新链
OLD_ONLOAD = "onload=\"if(this.dataset.src && !this.src.includes(this.dataset.src)){const temp=new Image();temp.onload=()=>{this.src=this.dataset.src;};temp.onerror=()=>{this.src='/images/default.jpg';};temp.src=this.dataset.src;}\""
NEW_ONLOAD = "onload=\"if(this.dataset.src && !this.src.includes(this.dataset.src)){const temp=new Image();temp.onload=()=>{this.src=this.dataset.src;};temp.onerror=()=>{this.src=this.dataset.fallback||'/images/default.jpg';};temp.src=this.dataset.src;}\""


def local_avatar(url: str) -> str:
    """https://avatar.tgnav.org/small/xxx.jpg → data-src 指向本地，fallback 指向字母头像。"""
    m = re.match(r"https://avatar\.tgnav\.org/small/([a-z0-9_]+)\.jpg", url)
    if not m:
        return url
    username = m.group(1)
    initial = username[0].upper() if username else "T"
    uiav = (
        f"https://ui-avatars.com/api/?name={initial}&background=random"
        "&size=128&font-size=0.45&bold=true"
    )
    return f"__AVATAR__{username}.jpg|{uiav}"


def main():
    # 1) 处理 HTML：data-src 头像 URL 换成本地路径，并加 data-fallback
    html_files = [
        p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
        if ".git" not in p
    ]
    dsr = re.compile(r'data-src="(https://avatar\.tgnav\.org/small/([a-z0-9_]+)\.jpg)"')
    onload_count = 0
    dsr_count = 0
    for path in html_files:
        with open(path, encoding="utf-8") as f:
            html = f.read()
        if "avatar.tgnav.org" not in html:
            continue

        def repl(m):
            username = m.group(2)
            initial = username[0].upper()
            uiav = (
                f"https://ui-avatars.com/api/?name={initial}&background=random"
                "&size=128&font-size=0.45&bold=true"
            )
            return f'data-src="/avatars/small/{username}.jpg" data-fallback="{uiav}"'

        new_html, n1 = dsr.subn(repl, html)
        n2 = new_html.count(OLD_ONLOAD)
        if n2:
            new_html = new_html.replace(OLD_ONLOAD, NEW_ONLOAD)
        if DRY:
            dsr_count += n1
            onload_count += n2
            continue
        if n1 or n2:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_html)
            dsr_count += n1
            onload_count += n2

    print(f"HTML: 头像 URL 替换 {dsr_count} 处, onload 兜底链更新 {onload_count} 处"
          + ("（dry-run 未写入）" if DRY else ""))

    # 2) 修补运行时 JS 模板（index.rDCzIqsL.js / go.CXiBLj0l.js）
    js_patches = {
        os.path.join(ROOT, "_astro", "index.rDCzIqsL.js"): (
            'const n=`https://avatar.tgnav.org/small/${e.username.toLowerCase()}.jpg`',
            'const n=`/avatars/small/${e.username.toLowerCase()}.jpg`,a9=`https://ui-avatars.com/api/?name=${e.username[0].toUpperCase()}&background=random&size=128&font-size=0.45&bold=true`',
        ),
        os.path.join(ROOT, "_astro", "go.CXiBLj0l.js"): (
            'l.src=`https://avatar.tgnav.org/small/${e.toLowerCase()}.jpg`',
            'l.src=`/avatars/small/${e.toLowerCase()}.jpg`,l.dataset.fallback=`https://ui-avatars.com/api/?name=${e[0].toUpperCase()}&background=random&size=128&font-size=0.45&bold=true`',
        ),
    }
    for js_path, (old, new) in js_patches.items():
        if not os.path.exists(js_path):
            print(f"JS: 未找到 {js_path}")
            continue
        with open(js_path, encoding="utf-8") as f:
            js = f.read()
        if old in js:
            # go.js 的 onerror 链随后把 src 设为 default.jpg，改为 fallback
            if Dry := False:
                pass
            if "l.onerror=()=>{l.onerror=null,l.src='" in js and "go.CXiBLj0l" in js_path:
                js = js.replace(
                    "l.onerror=()=>{l.onerror=null,l.src='/images/default.jpg'}",
                    "l.onerror=()=>{l.onerror=null,l.src=l.dataset.fallback||'/images/default.jpg'}",
                )
            if DRY:
                print(f"JS: {os.path.basename(js_path)} 命中 1 处（dry-run 未写入）")
            else:
                with open(js_path, "w", encoding="utf-8") as f:
                    f.write(js.replace(old, new))
                print(f"JS: {os.path.basename(js_path)} 已修补")
        else:
            print(f"JS: {os.path.basename(js_path)} 未命中目标片段")

    # 3) 输出唯一头像清单（fetch-avatars.py 的输入）
    usernames = set()
    for path in html_files:
        with open(path, encoding="utf-8") as f:
            for m in re.finditer(r'/avatars/small/([a-z0-9_]+)\.jpg', f.read()):
                usernames.add(m.group(1))
    if not DRY:
        os.makedirs(os.path.join(ROOT, "avatars", "small"), exist_ok=True)
        with open(os.path.join(ROOT, "avatars", "usernames.txt"), "w") as f:
            f.write("\n".join(sorted(usernames)))
        print(f"唯一头像清单: avatars/usernames.txt ({len(usernames)} 个)")
    else:
        print(f"唯一头像清单: {len(usernames)} 个")


if __name__ == "__main__":
    main()
