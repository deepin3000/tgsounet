#!/usr/bin/env python3
"""为 detail/ 详情页生成独特的 meta 描述，降低与原站模板文案的重复度。

数据源：每页 HTML 自身的 title/username/type/category/stats/description。
句式：6 套模板按 username 哈希轮换，确保同类页面描述各不相同。
同步更新：meta description、og:description、twitter:description、JSON-LD。
幂等：可重复运行。
"""
import html as htmllib
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DETAIL_DIR = os.path.join(ROOT, 'detail')

TITLE_CLEAN_RE = re.compile(r'\s*[-|]\s*Telegram[^|]*\|\s*TGSOU\s*$')
OLD_TEMPLATE_RE = re.compile(
    r'^Telegram (频道|群组|机器人) @([A-Za-z0-9_]+) \((.*)\) 的详情介绍与直达加入链接。'
    r'包含订阅成员数、更新时间及详细描述：'
)

# 每页提取四要素：type(频道/群组/机器人)、category、members(如 38.2K)、desc
# 生成模板围绕四要素重排，不再复用原站句式。

TYPE_LABEL = {'频道': 'Telegram 频道', '群组': 'Telegram 群组', '机器人': 'Telegram 机器人'}

TEMPLATES = [
    '{desc}——这是{name}（@{user}）的{cat}类{TG}，本站已收录其入口与档案，含订阅规模{members}与最近更新时间，可在 TGSOU 一键直达。',
    '在 TGSOU 查看{cat}类{TG}「{name}」（@{user}）的完整档案：{desc}订阅规模{members}，档案持续更新，站内搜索即可再次找到。',
    '{name}（@{user}）是一条{cat}方向的{TG}。简介：{desc}当前订阅规模约{members}，点进本页可获取直达链接与更多档案信息。',
    '想找{cat}类{TG}？「{name}」（@{user}）值得一试：{desc}TGSOU 收录了它的订阅规模（{members}）与更新记录，支持一键加入。',
    '本页是{TG}「{name}」（@{user}）的收录档案，归类于{cat}。{desc}规模数据：{members}；档案由 TGSOU 人工核验并保持更新。',
    '{cat}类{TG}「{name}」（@{user}）：{desc}在本页可查看订阅规模（{members}）、最近更新时间，并通过 TGSOU 直达入口加入。',
]

# 无成员数据（机器人/未采集）时的替代模板
TEMPLATES_NO_MEMBERS = [
    '{desc}——这是{name}（@{user}）的{cat}类{TG}，本站已收录其入口与档案，可在 TGSOU 一键直达。',
    '在 TGSOU 查看{cat}类{TG}「{name}」（@{user}）的完整档案：{desc}档案持续更新，站内搜索即可再次找到。',
    '{name}（@{user}）是一条{cat}方向的{TG}。简介：{desc}点进本页可获取直达链接与更多档案信息。',
    '想找{cat}类{TG}？「{name}」（@{user}）值得一试：{desc}TGSOU 收录了它的档案与更新记录，支持一键加入。',
    '本页是{TG}「{name}」（@{user}）的收录档案，归类于{cat}。{desc}档案由 TGSOU 人工核验并保持更新。',
    '{cat}类{TG}「{name}」（@{user}）：{desc}在本页可查看档案详情与最近更新时间，并通过 TGSOU 直达入口加入。',
]


def unescape_and_clean(text: str) -> str:
    text = htmllib.unescape(text)
    text = text.replace('\u00a0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_page(path: str):
    data = open(path, encoding='utf-8').read()

    m = re.search(r'<title>([^<]+)</title>', data)
    if not m:
        return None
    name = TITLE_CLEAN_RE.sub('', m.group(1)).strip()

    m = re.search(r'quick-stats-grid[^>]*>(.*?)</div>\s*</div>', data, re.S)
    members = ''
    type_badge = ''
    category = ''
    username = ''

    m = re.search(r'type-badge"[^>]*>\s*([^<]+?)\s*</span>', data)
    if m:
        type_badge = unescape_and_clean(m.group(1))
    m = re.search(r'category-badge"[^>]*>\s*([^<]+?)\s*</a>', data)
    if m:
        category = unescape_and_clean(m.group(1))
    m = re.search(r'/go/\?username=([A-Za-z0-9_]+)', data)
    if m:
        username = m.group(1)
    # members: first cell after 订阅/群员数
    m = re.search(r'订阅/群员数</span>.*?title-large[^>]*>([^<]+)<', data, re.S)
    if m:
        members = unescape_and_clean(m.group(1))

    # description block: content of 频道/群组/机器人简介与描述
    m = re.search(r'(频道|群组|机器人)简介与描述\s*</h3>\s*<div[^>]*body-large[^>]*>\s*(.*?)\s*</div>', data, re.S)
    desc = ''
    if m:
        desc = unescape_and_clean(m.group(2))
        desc = re.sub(r'\s*…$', '', desc)

    return {
        'name': name, 'username': username or os.path.basename(os.path.dirname(path)),
        'type': type_badge or '频道', 'category': category or '综合',
        'members': members or '未知规模', 'desc': desc,
        'raw': data,
    }


def build_description(entry: dict) -> str:
    tg = TYPE_LABEL.get(entry['type'], 'Telegram 频道')
    desc = entry['desc'] or '暂无官方简介。'
    # keep desc snippet modest to leave room for the sentence
    if len(desc) > 80:
        desc = desc[:80].rstrip() + '…'
    # ensure the desc clause ends with punctuation before the next sentence
    if not re.search(r'[。！？…」）.!?]$', desc):
        desc += '。'
    has_members = bool(entry['members']) and entry['members'] != '未知规模'
    tpl_set = TEMPLATES if has_members else TEMPLATES_NO_MEMBERS
    idx = sum(ord(c) for c in entry['username']) % len(tpl_set)
    out = tpl_set[idx].format(
        name=entry['name'], user=entry['username'], cat=entry['category'],
        TG=tg, members=entry['members'] or '', desc=desc,
    )
    # tidy spacing around numbers inserted into Chinese text
    out = re.sub(r'规模([0-9.]+[KkMm万]?)', r'规模 \1', out)
    # meta description best practice ≤ ~155 chars (CJK wider)
    return out[:180]


def replace_first(data: str, pattern: str, repl: str) -> str:
    return re.sub(pattern, repl, data, count=1)


def main():
    changed = skipped = 0
    for username in sorted(os.listdir(DETAIL_DIR)):
        path = os.path.join(DETAIL_DIR, username, 'index.html')
        if not os.path.isfile(path):
            continue
        entry = parse_page(path)
        if entry is None:
            continue
        data = entry['raw']
        old_m = re.search(r'<meta name="description" content="([^"]*)">', data)
        if not old_m:
            skipped += 1
            continue
        old_desc = old_m.group(1)
        if not OLD_TEMPLATE_RE.match(htmllib.unescape(old_desc)):
            skipped += 1  # already diversified
            continue

        new_desc = build_description(entry)
        esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        new_esc = esc(new_desc)

        data = replace_first(data, re.escape(f'<meta name="description" content="{old_desc}">'),
                             f'<meta name="description" content="{new_esc}">')
        data = replace_first(data, re.escape(f'<meta property="og:description" content="{old_desc}">'),
                             f'<meta property="og:description" content="{new_esc}">')
        data = replace_first(data, re.escape(f'<meta name="twitter:description" content="{old_desc}">'),
                             f'<meta name="twitter:description" content="{new_esc}">')
        # JSON-LD description (unescaped old)
        data = replace_first(data, re.escape(f'"description":"{old_desc}"'),
                             f'"description":"{new_desc.replace(chr(34), chr(39))}"')

        open(path, 'w', encoding='utf-8').write(data)
        changed += 1

    print(f'diversified: {changed}, skipped: {skipped}')


if __name__ == '__main__':
    main()
