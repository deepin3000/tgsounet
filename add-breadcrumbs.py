#!/usr/bin/env python3
"""为 detail/ 详情页添加面包屑导航与 BreadcrumbList 结构化数据。

改动：
1. 把「返回 xx 导航」单链接替换为 首页 › 频道/群组/机器人 › 分类 的三级面包屑
2. 在 JSON-LD（原有 WebPage schema）之后追加 BreadcrumbList schema

面包屑结构：
  首页(/) › 频道(/channel/) › 资讯新闻(/channel/资讯新闻/) › 当前页
当前页不放入 JSON-LD（Google 要求最后一项是当前页 URL，可省略最后项）。

幂等：检测到 breadcrumb-nav 或 BreadcrumbList 即跳过。
"""
import html as htmllib
import json
import os
import re
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
DETAIL_DIR = os.path.join(ROOT, 'detail')
BASE = 'https://www.tgsou.net'

BACK_LINK_RE = re.compile(
    r'<!-- Back Navigation --> <a href="/(channel|group|robot)/" class="md-button-text"'
    r' style="margin-bottom: 24px; display: inline-flex; align-items: center; gap: 8px;"'
    r' data-astro-cid-ow6kdzty> <i class="fa-solid fa-arrow-left" data-astro-cid-ow6kdzty></i>'
    r' 返回(频道|群组|机器人)导航\s*</a>'
)

TYPE_MAP = {'频道': ('channel', '频道导航'), '群组': ('group', '群组导航'), '机器人': ('robot', '机器人导航')}


def item(pos, name, url):
    return {'@type': 'ListItem', 'position': pos, 'name': name, 'item': BASE + url}

BREADCRUMB_STYLE = (
    'margin-bottom: 20px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;'
    ' font-size: 13.5px; color: var(--md-sys-color-on-surface-variant);'
)


def build_breadcrumb_html(slug_seg: str, type_label: str, cat_url: str, cat_name: str) -> str:
    seg_url, seg_name = TYPE_MAP[type_label]
    arrow = '<i class="fa-solid fa-angle-right" style="font-size: 11px; opacity: 0.55;"></i>'
    home = f'<a href="/" class="md-button-text" style="padding: 0; font-size: inherit; color: inherit; opacity: 0.85;">首页</a>'
    seg = f'<a href="/{seg_url}/" class="md-button-text" style="padding: 0; font-size: inherit; color: inherit; opacity: 0.85;">{seg_name}</a>'
    cat = f'<a href="{cat_url}" class="md-button-text" style="padding: 0; font-size: inherit; color: var(--md-sys-color-primary);">{htmllib.escape(cat_name)}</a>'
    cur = f'<span style="opacity: 0.9; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{TITLE}}</span>'
    return (f'<!-- Breadcrumb Navigation --> <nav aria-label="面包屑" class="breadcrumb-nav" style="{BREADCRUMB_STYLE}">'
            f'{home} {arrow} {seg} {arrow} {cat} {arrow} {cur}</nav>')


def main():
    changed = skipped = no_ld = 0
    for d in sorted(os.listdir(DETAIL_DIR)):
        path = os.path.join(DETAIL_DIR, d, 'index.html')
        if not os.path.isfile(path):
            continue
        data = open(path, encoding='utf-8').read()

        if 'breadcrumb-nav' in data or 'BreadcrumbList' in data:
            skipped += 1
            continue

        m = BACK_LINK_RE.search(data)
        if not m:
            skipped += 1
            continue
        seg_url, type_label = m.group(1), m.group(2)

        mc = re.search(r'<a href="(/(?:channel|group|robot)/[^"]+/)" class="label-large category-badge"[^>]*>\s*([^<]+?)\s*</a>', data)
        if not mc:
            # anchor-style category (e.g. /channel/#vps主机) -> no dedicated category page exists;
            # use the type listing page as the last crumb instead
            mc2 = re.search(r'<a href="(/(?:channel|group|robot)/#[^"]*?)" class="label-large category-badge"[^>]*>\s*([^<]+?)\s*</a>', data)
            mt0 = re.search(r'type-badge"[^>]*>\s*([^<]+?)\s*</span>', data)
            title_m0 = re.search(r'<title>([^<]+)</title>', data)
            if not (mc2 and mt0 and title_m0):
                skipped += 1
                continue
            type_badge0 = mt0.group(1).strip()
            short_title0 = title_m0.group(1).split(' - ')[0].split(' | ')[0]
            seg_url0, seg_name0 = TYPE_MAP[type_label]
            arrow = '<i class="fa-solid fa-angle-right" style="font-size: 11px; opacity: 0.55;"></i>'
            style_a = 'padding: 0; font-size: inherit; color: inherit; opacity: 0.85;'
            crumb_html = (f'<!-- Breadcrumb Navigation --> <nav aria-label="面包屑" class="breadcrumb-nav" style="{BREADCRUMB_STYLE}">'
                          f'<a href="/" class="md-button-text" style="{style_a}">首页</a> {arrow} '
                          f'<a href="/{seg_url0}/" class="md-button-text" style="{style_a}">{seg_name0}</a> {arrow} '
                          f'<span style="opacity: 0.9; max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{htmllib.escape(short_title0)}</span></nav>')
            data = BACK_LINK_RE.sub(lambda _: crumb_html, data, count=1)

            crumb_ld = {
                '@context': 'https://schema.org',
                '@type': 'BreadcrumbList',
                'itemListElement': [
                    item(1, '首页', '/'),
                    item(2, seg_name0, f'/{seg_url0}/'),
                ],
            }
            ld_json = json.dumps(crumb_ld, ensure_ascii=False, separators=(',', ':'))
            m_ld = re.search(r'(<script type="application/ld\+json">\{.*?\}</script>)', data, re.S)
            if m_ld:
                insert_at = m_ld.end()
                data = data[:insert_at] + f' <script type="application/ld+json">{ld_json}</script>' + data[insert_at:]
                open(path, 'w', encoding='utf-8').write(data)
                changed += 1
            else:
                skipped += 1
            continue

        mt = re.search(r'type-badge"[^>]*>\s*([^<]+?)\s*</span>', data)
        title_m = re.search(r'<title>([^<]+)</title>', data)
        if not (mc and mt and title_m):
            skipped += 1
            continue

        cat_url_raw = mc.group(1)
        cat_name = htmllib.unescape(mc.group(2).strip())
        type_badge = mt.group(1).strip()
        page_title = title_m.group(1).strip()

        # safety: category path prefix must match the type segment
        if not cat_url_raw.startswith(f'/{seg_url}/'):
            skipped += 1
            continue

        # breadcrumb HTML with the visible current page title
        crumb_html = build_breadcrumb_html(seg_url, type_label, cat_url_raw, cat_name)
        short_title = page_title.split(' - ')[0].split(' | ')[0]
        crumb_html = crumb_html.replace('{TITLE}', htmllib.escape(short_title))
        data = BACK_LINK_RE.sub(lambda _: crumb_html, data, count=1)

        # BreadcrumbList JSON-LD: 首页 › 类型导航 › 分类
        crumb_ld = {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': [
                item(1, '首页', '/'),
                item(2, TYPE_MAP[type_badge][1] if type_badge in TYPE_MAP else TYPE_MAP[type_label][1], f'/{TYPE_MAP[type_label][0]}/'),
                item(3, cat_name, cat_url_raw),
            ],
        }
        ld_json = json.dumps(crumb_ld, ensure_ascii=False, separators=(',', ':'))

        # append right after the existing WebPage JSON-LD block
        m_ld = re.search(r'(<script type="application/ld\+json">\{.*?\}</script>)', data, re.S)
        if m_ld:
            insert_at = m_ld.end()
            data = data[:insert_at] + f' <script type="application/ld+json">{ld_json}</script>' + data[insert_at:]
        else:
            # no existing JSON-LD: put before </head>
            tag = f'<script type="application/ld+json">{ld_json}</script>'
            if '</head>' in data:
                data = data.replace('</head>', tag + '</head>', 1)
                no_ld += 1
            else:
                skipped += 1
                # rollback breadcrumb-only change for consistency
                continue

        open(path, 'w', encoding='utf-8').write(data)
        changed += 1

    print(f'breadcrumbs added: {changed}, skipped: {skipped}, injected-head-only: {no_ld}')


if __name__ == '__main__':
    main()
