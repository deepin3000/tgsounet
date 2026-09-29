#!/usr/bin/env python3
"""监听 HTML 变更，自动重建 TGSOU 搜索索引并提示。

用法:  python3 watch-search-index.py
依赖:  仅标准库（macOS/Linux 通用；Linux 需系统装有 inotifywait 或退化为轮询）
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build-search-index.py"
WATCH_DIRS = ["detail", "channel", "group", "robot"]
DEBOUNCE = 3.0  # 秒：变化停止后延迟重建
POLL_INTERVAL = 2.0

try:
    import termcolor  # 可选
    def tint(s, c): return termcolor.colored(s, c)
except ImportError:
    def tint(s, c): return s


def snapshot():
    state = {}
    for d in WATCH_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("index.html"):
            st = p.stat()
            state[str(p.relative_to(ROOT))] = st.st_mtime_ns, st.st_size
    return state


def rebuild(reason: str):
    print(tint(f"\n[{time.strftime('%H:%M:%S')}] 检测到变更（{reason}），重建索引…", "cyan"))
    t0 = time.time()
    r = subprocess.run([sys.executable, str(BUILD)], cwd=ROOT)
    dt = time.time() - t0
    if r.returncode == 0:
        print(tint(f"✔ 索引已更新（{dt:.1f}s）。刷新页面即可使用新搜索结果。", "green"))
    else:
        print(tint("✘ 索引构建失败，请检查上方报错。", "red"))


def try_fsevents():
    """macOS 优先用 FSEvents（标准库无法直接用，尝试第三方；失败返回 None）。"""
    try:
        from watchdog.observers import Observer  # noqa: F401
        from watchdog.events import FileSystemEventHandler

        class H(FileSystemEventHandler):
            def __init__(self):
                self.timer = None
                self.lock = threading.Lock()

            def on_any_event(self, event):
                if event.is_directory or not str(event.src_path).endswith(".html"):
                    return
                with self.lock:
                    if self.timer:
                        self.timer.cancel()
                    self.timer = threading.Timer(DEBOUNCE, rebuild, args=[Path(event.src_path).name])
                    self.timer.start()

        return H()
    except ImportError:
        return None


def watch_poll():
    """跨平台兜底：轮询 mtime/size。"""
    print(tint("使用轮询模式监听（每 %ds）。" % POLL_INTERVAL, "yellow"))
    last = snapshot()
    while True:
        time.sleep(POLL_INTERVAL)
        now = snapshot()
        added = set(now) - set(last)
        removed = set(last) - set(now)
        changed = {k for k in (set(now) & set(last)) if now[k] != last[k]}
        if added or removed or changed:
            reason = []
            if added:
                reason.append(f"新增 {len(added)}")
            if removed:
                reason.append(f"删除 {len(removed)}")
            if changed:
                reason.append(f"修改 {len(changed)}")
            last = now
            rebuild("、".join(reason))


def main():
    print(tint("TGSOU 索引监听已启动（Ctrl+C 退出）", "green"))
    rebuild("初始构建")
    handler = try_fsevents()
    if handler:
        from watchdog.observers import Observer
        obs = Observer()
        for d in WATCH_DIRS:
            p = ROOT / d
            if p.exists():
                obs.schedule(handler, str(p), recursive=True)
        obs.start()
        print(tint("watchdog 实时监听模式。", "green"))
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            obs.stop()
            obs.join()
    else:
        watch_poll()


if __name__ == "__main__":
    main()
