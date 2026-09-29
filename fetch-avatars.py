#!/usr/bin/env python3
"""抓取频道/群组/机器人的真实头像到 avatars/small/。

三种方式（按优先级自动选择，也可用 --method 指定）：

  1. bot    —— Telegram Bot API（推荐）
     需要一个 Bot Token（@BotFather 创建，免费）：--token 123:ABC
     原理：getUserProfilePhotos 需要 user id，机器人无法直接按用户名查；
           但 getChat 在机器人是频道/群组成员时可用。覆盖范围有限。
     优点：稳定、官方 API、可拿到高清 photo_big。

  2. scrape —— 解析 https://t.me/{username} 公开页的 og:image
     无需任何凭证，覆盖所有公开频道/群组。
     og:image 指向 cdn*.cdn-telegram.org 的真实头像 JPG。
     缺点：对部分机器人（bot 无公开页面头像）拿不到；需控制请求频率。

  3. telethon —— MTProto 用户账号 API（覆盖最全，可选）
     pip install telethon，需 api_id/api_hash（my.telegram.org 免费申请）
     DownloadProfilePhoto 拿到的就是频道/群组/用户头像原图。

用法示例:
  python3 fetch-avatars.py --method scrape
  python3 fetch-avatars.py --method bot --token 123456:ABC-DEF
  python3 fetch-avatars.py --method scrape --limit 100
  python3 fetch-avatars.py --method telethon --api-id 123 --api-hash xxx
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
from typing import Optional

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "avatars", "small")
LIST_FILE = os.path.join(ROOT, "avatars", "usernames.txt")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def load_usernames() -> list:
    if not os.path.exists(LIST_FILE):
        print("缺少 avatars/usernames.txt —— 先运行 migrate-avatars.py")
        sys.exit(1)
    with open(LIST_FILE) as f:
        names = [ln.strip() for ln in f if ln.strip()]
    # 已有本地的跳过
    return [n for n in names if not os.path.exists(os.path.join(OUT_DIR, f"{n}.jpg"))]


def fetch(url: str, timeout: int = 10, retries: int = 3) -> Optional[bytes]:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(0.5 * (attempt + 1))
    return None


# ---------- 方式 1: Bot API ----------
def fetch_via_bot(usernames: list, token: str) -> dict:
    ok, fail = 0, 0
    api = f"https://api.telegram.org/bot{token}"
    for i, name in enumerate(usernames):
        info = fetch(f"{api}/getChat?chat_id=@{name}")
        if not info:
            fail += 1
            continue
        data = json.loads(info)
        chat = data.get("result") or {}
        if not chat.get("photo") and not chat.get("id"):
            fail += 1
            continue
        # Bot API 不直接给头像文件；getChat 拿到 chat 后用 getUserProfilePhotos 仅适用用户。
        # 频道头像需 Bot 是成员才有 photo 字段。有 photo 时取 big_file_id。
        photo = chat.get("photo") or {}
        file_id = photo.get("big_file_id") or photo.get("small_file_id")
        if not file_id:
            fail += 1
            continue
        fpath = json.loads(fetch(f"{api}/getFile?file_id={file_id}") or "{}")
        file_path = (fpath.get("result") or {}).get("file_path")
        if not file_path:
            fail += 1
            continue
        blob = fetch(f"https://api.telegram.org/file/bot{token}/{file_path}")
        if blob:
            with open(os.path.join(OUT_DIR, f"{name}.jpg"), "wb") as f:
                f.write(blob)
            ok += 1
        else:
            fail += 1
        if i % 25 == 0:
            print(f"  进度 {i}/{len(usernames)} 成功 {ok} 失败 {fail}")
        time.sleep(0.15)
    return {"ok": ok, "fail": fail}


# ---------- 方式 2: t.me 页面 og:image ----------
OG_RE = re.compile(r'<meta property="og:image" content="([^"]+)"')


def fetch_via_scrape(usernames: list) -> dict:
    ok, fail, skip = 0, 0, 0

    def one(name):
        nonlocal ok, fail, skip
        html = fetch(f"https://t.me/{name}", timeout=8)
        if not html:
            fail += 1
            return
        m = OG_RE.search(html.decode("utf-8", "ignore"))
        if not m:
            skip += 1  # 页面存在但无头像（常见于 bot）
            return
        img_url = m.group(1)
        # t.me 的真实头像在 cdn*.telesco.pe / cdn*.cdn-telegram.org；data:image/svg 是默认字母图，跳过
        if not ("telesco.pe" in img_url or "cdn-telegram.org" in img_url):
            skip += 1
            return
        blob = fetch(img_url, timeout=10)
        if blob and blob[:3] == b"\xff\xd8\xff":  # JPEG magic
            with open(os.path.join(OUT_DIR, f"{name}.jpg"), "wb") as f:
                f.write(blob)
            ok += 1
        else:
            fail += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for i, _ in enumerate(ex.map(one, usernames)):
            if i % 50 == 0 and i:
                print(f"  进度 {i}/{len(usernames)}")
    return {"ok": ok, "fail": fail, "no_avatar": skip}


# ---------- 方式 3: Telethon ----------
def fetch_via_telethon(usernames: list, api_id: int, api_hash: str) -> dict:
    try:
        from telethon.sync import TelegramClient
        from telethon.errors import FloodWaitError
    except ImportError:
        print("需要安装: pip install telethon")
        sys.exit(1)
    ok, fail = 0, 0
    with TelegramClient("tgsou_session", api_id, api_hash) as client:
        for i, name in enumerate(usernames):
            try:
                entity = client.get_entity(f"https://t.me/{name}")
                path = client.download_profile_photo(entity, file=os.path.join(OUT_DIR, f"{name}.jpg"))
                if path:
                    ok += 1
                else:
                    fail += 1
            except FloodWaitError as e:
                print(f"  触发限流，等待 {e.seconds}s…")
                time.sleep(e.seconds + 1)
            except Exception:
                fail += 1
            if i % 25 == 0:
                print(f"  进度 {i}/{len(usernames)} 成功 {ok} 失败 {fail}")
    return {"ok": ok, "fail": fail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", choices=["scrape", "bot", "telethon"], default="scrape")
    ap.add_argument("--token", help="Bot Token（bot 方式）")
    ap.add_argument("--api-id", type=int, help="Telethon api_id")
    ap.add_argument("--api-hash", help="Telethon api_hash")
    ap.add_argument("--limit", type=int, default=0, help="只抓前 N 个")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    usernames = load_usernames()
    if args.limit:
        usernames = usernames[: args.limit]
    if not usernames:
        print("所有头像均已就绪，无需抓取。")
        return
    print(f"待抓取 {len(usernames)} 个头像（方式: {args.method}）")

    if args.method == "scrape":
        stat = fetch_via_scrape(usernames)
    elif args.method == "bot":
        if not args.token:
            print("bot 方式需要 --token"); sys.exit(1)
        stat = fetch_via_bot(usernames, args.token)
    else:
        if not args.api_id or not args.api_hash:
            print("telethon 方式需要 --api-id 和 --api-hash"); sys.exit(1)
        stat = fetch_via_telethon(usernames, args.api_id, args.api_hash)

    print("完成:", stat)
    total = len([f for f in os.listdir(OUT_DIR) if f.endswith(".jpg")])
    print(f"avatars/small/ 现有 {total} 个真实头像，其余将走 ui-avatars 字母兜底。")


if __name__ == "__main__":
    main()
