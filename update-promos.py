#!/usr/bin/env python3
"""把所有页面的内联 adPool 数组替换为引用 /promos.js 的统一脚本标签。

改动内容：
1. 首页等页面：<script>(function(){const adPool = [...];window.adPool = adPool;})();</script>
   → <script src="/promos.js"></script><script>window.adPool = window.adPoolData;</script>
2. 详情页推广内联数组同理替换。
3. 若页面既无内联 adPool 也无 promos.js 引用（如 about），在 </head> 前补引用，
   保证 /go/ 等特殊页面也可统一管理。

幂等：已引用 promos.js 的页面跳过。
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SNIPPET = '<script src="/promos.js"></script><script>window.adPool=window.adPoolData;</script>'
INLINE_RE = re.compile(
    r'<script>\(function\(\)\{const adPool = \[.*?\];\s*window\.adPool = adPool;\s*\}\)\(\);</script>',
    re.S,
)
# 首页等页面：adPool 与 cleanXxxPool 共用一个 <script>，只替换尾部 adPool 段
INLINE_TAIL_RE = re.compile(
    r'const adPool = \[.*?\];\\n\s*window\.adPool = adPool;',
    re.S,
)


def process(path: str) -> str:
    data = open(path, encoding='utf-8').read()
    if '/promos.js' in data:
        return 'skip'
    if INLINE_RE.search(data):
        data = INLINE_RE.sub(SNIPPET, data, count=1)
        open(path, 'w', encoding='utf-8').write(data)
        return 'replaced'
    if INLINE_TAIL_RE.search(data):
        # replace only the adPool tail inside a shared script; keep pools + expose hook
        data = INLINE_TAIL_RE.sub('window.adPoolData = [];window.adPool = window.adPoolData;', data, count=1)
        # inject promos.js BEFORE this script so adPoolData is defined (script executes in order)
        i = data.find('window.adPoolData = []')
        start = data.rfind('<script>', 0, i)
        data = data[:start] + SNIPPET + data[start:]
        open(path, 'w', encoding='utf-8').write(data)
        return 'replaced'
    # no inline pool and no reference: inject into head (keep render scripts working)
    if '</head>' in data:
        data = data.replace('</head>', SNIPPET + '</head>', 1)
        open(path, 'w', encoding='utf-8').write(data)
        return 'injected'
    return 'no-head'


def main():
    counts = {'replaced': 0, 'injected': 0, 'skip': 0, 'no-head': 0}
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('_astro', 'avatars', 'search', '.git')]
        for fn in files:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, ROOT)
            result = process(path)
            counts[result] += 1
            if result in ('replaced', 'injected'):
                pass
    print(counts)


if __name__ == '__main__':
    main()
