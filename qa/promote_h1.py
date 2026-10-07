# -*- coding: utf-8 -*-
"""Promote the page-header headline from <h2> to <h1> across category/detail template pages.

Only the FIRST `<h2 class="headline-medium"> ... </h2>` block of each file is touched.
Idempotent: files already using h1 in that position are left unchanged.
"""
import io
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
DIRS = ["channel", "group", "robot", "enroll"]
PAT = re.compile(r'<h2 class="headline-medium"([^>]*)>(.*?)</h2>', re.S)


def promote(path):
    s = io.open(path, encoding="utf-8").read()
    if '<h1 class="headline-medium">' in s:
        return "skip-h1"
    m = PAT.search(s)
    if not m:
        return "no-h2"
    s = s[:m.start()] + '<h1 class="headline-medium"' + m.group(1) + ">" + m.group(2) + "</h1>" + s[m.end():]
    io.open(path, "w", encoding="utf-8").write(s)
    return "ok"


def main():
    counts = {"ok": 0, "skip-h1": 0, "no-h2": 0}
    for d in DIRS:
        dp = os.path.join(ROOT, d)
        if not os.path.isdir(dp):
            continue
        for dirpath, _dirnames, filenames in os.walk(dp):
            for fn in filenames:
                if fn == "index.html":
                    rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
                    res = promote(os.path.join(dirpath, fn))
                    counts[res] = counts.get(res, 0) + 1
                    if res == "no-h2":
                        print("no-h2:", rel)
    print(counts)


if __name__ == "__main__":
    main()
