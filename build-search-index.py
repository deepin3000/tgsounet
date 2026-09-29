#!/usr/bin/env python3
"""从本地静态页面构建 TGSOU 站内搜索索引。

用法:  python3 build-search-index.py
输出:  search/search-index.json (元数据+常用条目)
       search/chunks/chunk-0.json ... (其余条目，前端懒加载)
"""
import glob
import json
import os
import re
import sys
from collections import Counter
from html import unescape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "search")
CHUNK_DIR = os.path.join(OUT_DIR, "chunks")
CHUNK_SIZE = 400

TYPE_NAMES = {"channel": "频道", "group": "群组", "robot": "机器人"}
TITLE_CLEAN_RE = re.compile(
    r"\s*[-|]\s*Telegram(?:频道|群组|机器人|导航)?\s*[-|]?\s*TGSOU\s*$", re.IGNORECASE
)


def strip_html(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def extract(path: str):
    html = open(path, encoding="utf-8").read()
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    if not m:
        return None
    title = TITLE_CLEAN_RE.sub("", unescape(m.group(1))).strip()
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    desc = unescape(m.group(1)) if m else ""
    m = re.search(r'<meta property="og:url" content="([^"]*)"', html)
    url = m.group(1) if m else None
    if not url:
        return None
    path_part = unescape(url).replace("https://tgsou.net", "", 1)
    if not path_part.startswith("/"):
        path_part = "/" + path_part
    username = ""
    if path_part.startswith("/detail/"):
        username = path_part.split("/")[2].lower()
    # 类型徽标与分类
    typ, category = "", ""
    m = re.search(r'type-badge[^>]*>\s*([^<]+?)\s*</span>', html)
    if m:
        typ = strip_html(m.group(1))
    m = re.search(r'category-badge"[^>]*>\s*([^<]+?)\s*</a>', html)
    if m:
        category = strip_html(m.group(1))
    return {
        "t": title,
        "d": desc[:160],
        "u": path_part,
        "id": username,
        "ty": typ,
        "c": category,
    }


def main():
    os.makedirs(CHUNK_DIR, exist_ok=True)
    # 清理旧分块
    for old in glob.glob(os.path.join(CHUNK_DIR, "chunk-*.json")):
        os.remove(old)

    docs, seen = [], set()
    for path in sorted(glob.glob(os.path.join(ROOT, "detail", "*", "index.html"))):
        doc = extract(path)
        if doc and doc["id"] and doc["id"] not in seen:
            seen.add(doc["id"])
            docs.append(doc)

    print(f"索引条目: {len(docs)}")

    # 常用条目 = 标题出现高频词打分（近似“热门”，仅用于首屏候选）
    counter = Counter()
    for d in docs:
        for ch in "ai大资源分享学习影视新闻科技工具":
            if ch in d["t"].lower() or ch in d["t"]:
                counter[ch] += 1
    common = [
        d
        for d in docs
        if any(kw in d["t"].lower() for kw in ("ai", "资源", "分享", "学习", "影视", "新闻", "科技", "工具", "tg", "telegram"))
    ][:400]

    meta = {
        "version": 1,
        "site": "TGSOU",
        "total": len(docs),
        "chunks": [],
        "commonCount": len(common),
    }
    with open(os.path.join(OUT_DIR, "search-index.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "common": common}, f, ensure_ascii=False, separators=(",", ":"))

    rest = docs[len(common):]
    for i in range(0, len(rest), CHUNK_SIZE):
        name = f"chunk-{i // CHUNK_SIZE}.json"
        with open(os.path.join(CHUNK_DIR, name), "w", encoding="utf-8") as f:
            json.dump(rest[i : i + CHUNK_SIZE], f, ensure_ascii=False, separators=(",", ":"))
        meta["chunks"].append(f"/search/chunks/{name}")

    # 重写一次以写入 chunks 列表
    with open(os.path.join(OUT_DIR, "search-index.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "common": common}, f, ensure_ascii=False, separators=(",", ":"))

    total = sum(os.path.getsize(p) for p in glob.glob(os.path.join(OUT_DIR, "**", "*.json"), recursive=True))
    print(f"索引体积: {total/1024:.0f} KB, 分块: {len(meta['chunks'])}")
    print(f"输出目录: {os.path.relpath(OUT_DIR, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
