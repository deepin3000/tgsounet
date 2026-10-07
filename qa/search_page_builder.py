# -*- coding: utf-8 -*-
"""Build /search/index.html for TGSOU from the detail-page skeleton (botfather snapshot).

Inputs (regenerate from a live snapshot if templates change):
  /tmp/seg1.html  - body start .. right before <main>
  /tmp/seg2.html  - from </main> .. end of page
  /tmp/head.html  - detail page head (used only for its icon..css tail)
Output:
  tgnav/search/index.html
"""
import os

seg1 = open("/tmp/seg1.html", encoding="utf-8").read()
seg2 = open("/tmp/seg2.html", encoding="utf-8").read()
head = open("/tmp/head.html", encoding="utf-8").read()

title = "TG中文搜索入口 - TGSOU 站内搜索 Telegram频道、群组、机器人"
desc = ("TGSOU 站内搜索入口：免费 TG中文搜索 工具，输入关键词即可搜索 Telegram 电报频道、"
        "群组、机器人，覆盖20000+热门中文资源，支持 TG搜 关键词直达收录档案。")
kw = ("TG中文搜索, TG搜索, tg搜, TGSOU站内搜索, Telegram搜索, 电报搜索, "
      "Telegram频道, Telegram群组, Telegram机器人, TG索引, 电报索引")

tail_from_icon = head[head.find('<link rel="icon"'):]
seo_head = (
    '<!DOCTYPE html><html lang="zh-CN"> <head><meta charset="UTF-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">'
    "<title>" + title + "</title>"
    '<meta name="description" content="' + desc + '">'
    '<meta name="keywords" content="' + kw + '">'
    '<meta name="author" content="TGSOU">'
    "<!-- Open Graph / Facebook -->"
    '<meta property="og:type" content="website">'
    '<meta property="og:url" content="https://tgsou.net/search/">'
    '<link rel="canonical" href="https://tgsou.net/search/">'
    '<meta property="og:title" content="' + title + '">'
    '<meta property="og:description" content="' + desc + '">'
    '<meta property="og:image" content="https://tgsou.net/images/logo.png">'
    "<!-- Twitter -->"
    '<meta property="twitter:card" content="summary">'
    '<meta property="twitter:url" content="https://tgsou.net/search/">'
    '<meta property="twitter:title" content="' + title + '">'
    '<meta property="twitter:description" content="' + desc + '">'
    '<meta property="twitter:image" content="https://tgsou.net/images/logo.png">'
)
new_head = seo_head + tail_from_icon

schema = ('{"@context":"https://schema.org","@type":"WebSite","name":"TGSOU",'
          '"alternateName":["TG中文搜索","TG搜","tgso电报搜索","电报搜索"],'
          '"url":"https://tgsou.net/","inLanguage":"zh-CN",'
          '"description":"TGSOU（tgsou.net）是专业的 TG中文搜索 平台，免费搜索和导航 Telegram 电报频道、群组、机器人，收录20000+热门中文资源。",'
          '"publisher":{"@type":"Organization","name":"TGSOU","url":"https://tgsou.net/",'
          '"logo":{"@type":"ImageObject","url":"https://tgsou.net/images/logo.png"}},'
          '"potentialAction":{"@type":"SearchAction","target":{"@type":"EntryPoint",'
          '"urlTemplate":"https://tgsou.net/search/?q={search_term_string}",'
          '"actionPlatform":["http://schema.org/DesktopWebPlatform","http://schema.org/MobileWebPlatform"]},'
          '"query-input":"required name=search_term_string"}}')

main = ('<!-- Main Workspace --> <main class="md-content"> <div class="page-container"> '
        '<header class="page-header"> <h1 class="headline-medium"> '
        '<i class="fa-solid fa-magnifying-glass" style="margin-right: 8px;"></i>站内搜索 </h1> '
        '<p class="body-medium page-subtitle"> 使用 TGSOU 站内搜索引擎，快速找到你需要的 Telegram 频道、群组与机器人。 </p> '
        '</header><!-- SEO: WebSite + Sitelinks SearchBox 结构化数据（与首页一致） --> '
        '<script type="application/ld+json">' + schema + "</script> "
        '<div class="page-article body-medium" style="max-width: 860px; margin: 0 auto;"> '
        "<p>TGSOU（tgsou.net）站内搜索入口：输入<strong>频道名</strong>、<strong>用户名</strong>或<strong>关键词</strong>"
        "（如「软件」「影视」「AI」「贴纸」「壁纸」）即可搜索全站收录的 Telegram 频道、群组与机器人档案，"
        '结果直达详情页（如 <a href="/detail/botfather/">@botfather</a>）。'
        "TGSOU 支持中文、拼音与中英混合的 <strong>TG中文搜索</strong>，"
        "一个输入框即可直达全站收录的电报资源，是轻量好用的 TG搜索 工具。</p> "
        '<div id="search-page-input-wrap" style="margin: 18px auto 26px; display: flex; align-items: center; gap: 10px; '
        'max-width: 560px; background: var(--glass-bg, rgba(255,255,255,.6)); border: 1px solid var(--glass-border, #ccc); '
        'border-radius: 24px; padding: 4px 8px 4px 20px;"> '
        '<i class="fa-solid fa-magnifying-glass" style="color: var(--md-sys-color-primary, #08c);"></i> '
        '<input id="search-page-input" type="text" placeholder="在 TGSOU 搜索：输入关键词，如 软件、AI、壁纸..." '
        'autocomplete="off" style="flex: 1; border: none; outline: none; background: transparent; '
        'color: var(--md-sys-color-on-surface, #333); font-size: 15px; padding: 10px 0; min-width: 0;"> '
        '<button id="search-page-go" style="width:auto;padding:9px 20px;border-radius:14px;'
        'border:1px solid var(--glass-border,#ccc);background:var(--md-sys-color-primary,#08c);color:#fff;'
        'font-size:13.5px;font-weight:700;cursor:pointer;flex-shrink:0;">搜索</button> </div> '
        '<div id="search-page-results" style="display: grid; grid-template-columns: 1fr; gap: 10px; margin-bottom: 26px;"></div> '
        '<noscript><div style="line-height:2;border:1px solid var(--glass-border,#ccc);border-radius:12px;padding:14px 18px;">'
        "<strong>热门收录直达：</strong> "
        '<a href="/detail/botfather/">BotFather</a>、<a href="/detail/adclose/">AdClose Official</a>、'
        '<a href="/detail/ednovas2/">EdNovas的小站</a>、<a href="/detail/pixiv_top50/">PIXIV站每日Top50</a>、'
        '<a href="/detail/teslacn/">Tesla News</a>、<a href="/detail/ai_copilot_channel/">AI Copilot</a>、'
        '<a href="/detail/guochandonghua/">国产动画资源库</a>。'
        "<br>启用 JavaScript 后可使用完整 TG中文搜索 功能。</div></noscript> "
        '<p style="opacity: .8; font-size: 13px;">找不到想要的？试试 <a href="/random/">随机探索</a>，'
        '或到 <a href="/enroll/">提交收录</a> 页推荐资源；也可以直接用页顶搜索框（Ctrl + K）。</p> '
        "</div> </div>")

JS_LINES = [
    '  function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}',
    '  var input=document.getElementById("search-page-input"),go=document.getElementById("search-page-go"),wrap=document.getElementById("search-page-results");',
    '  if(!input||!go||!wrap)return;',
    '  function load(cb){',
    '    if(window.__tgsouIndex){cb(window.__tgsouIndex);return;}',
    '    fetch("search-index.json",{credentials:"omit"}).then(function(r){if(!r.ok)throw new Error(0);return r.json();}).then(function(d){',
    '      var urls=((d.meta&&d.meta.chunks)||[]).map(function(u){return String(u).replace(/^\\/search\\//,"");});',
    '      var all=(d.common||[]).slice();',
    '      if(!urls.length)return all;',
    '      return Promise.all(urls.map(function(u){return fetch(u,{credentials:"omit"}).then(function(r){return r.json();});})).then(function(chunks){chunks.forEach(function(c){if(Array.isArray(c))all=all.concat(c);});return all;});',
    '    }).then(function(all){window.__tgsouIndex=all;cb(all);}).catch(function(){',
    'wrap.innerHTML=\'<p style="text-align:center;opacity:.6;padding:30px 0;">搜索服务暂不可用，请稍后再试或使用顶部搜索框（Ctrl+K）。</p>\';});',
    '  }',
    '  function score(doc,terms){',
    '    var s=0,t=(doc.t||"").toLowerCase(),d=(doc.d||"")+"",u=(doc.u||"").toLowerCase(),id=(doc.id||"").toLowerCase();',
    '    for(var i=0;i<terms.length;i++){var w=terms[i].toLowerCase();if(!w)continue;',
    '      if(t.indexOf(w)>=0)s+=30;if(id.indexOf(w)>=0)s+=18;if(u.indexOf(w)>=0)s+=14;if(d.indexOf(w)>=0)s+=6;}',
    '    return s;',
    '  }',
    '  function clean(x){var t=String(x.t||x.name||"");var i=t.indexOf(" - Telegram");if(i>0)t=t.slice(0,i);return t;}',
    '  function render(q,docs){',
    '    if(!docs.length){wrap.innerHTML=\'<p style="text-align:center;opacity:.6;padding:30px 0;">未找到与「\'+esc(q)+\'」相关的内容。换个关键词试试，或到 <a href="/enroll/">提交收录</a> 推荐给我们。</p>\';return;}',
    '    wrap.innerHTML=docs.map(function(x){',
    '      var ty=x.ty||x.type||"";var cls=ty==="频道"?"channel":ty==="群组"?"group":"robot";',
    '      var desc=String(x.d||"").slice(0,70);',
    '      return \'<a class="latest-card-item" href="\'+esc(x.u||x.url||"#")+\'" style="padding:12px 14px;">\'',
    '        +\'<div class="latest-card-meta" style="gap:4px;min-width:0;"><div style="display:flex;align-items:center;gap:8px;"><span class="latest-card-title" style="white-space:normal;flex:1;">\'+esc(clean(x))+\'</span>\'',
    '        +\'<span class="latest-type-badge label-\'+cls+\'" style="flex-shrink:0;">\'+esc(ty||"详情")+\'</span></div>\'',
    '        +\'<p class="latest-card-desc" style="white-space:normal;height:auto;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;">\'+esc(desc)+\'</p></div>\'',
    '        +\'</a>\';',
    '    }).join("");',
    '  }',
    '  function run(){',
    '    var q=input.value.replace(/^\\s+|\\s+$/g,"");',
    '    try{history.replaceState(null,"",location.pathname+(q?"?q="+encodeURIComponent(q):""));}catch(e){}',
    '    document.title=q?("「"+q+"」 - TGSOU TG中文搜索站内搜索"):"TG中文搜索 - TGSOU 站内搜索";',
    '    if(!q){wrap.innerHTML=\'<p style="text-align:center;opacity:.6;padding:30px 0;">输入关键词开始搜索。热门：软件、影视、AI、二次元、贴纸、壁纸。</p>\';return;}',
    '    load(function(all){',
    '      var terms=q.split(/\\s+/);var res=[];',
    '      for(var i=0;i<all.length;i++){var s=score(all[i],terms);if(s>0)res.push([s,i,all[i]]);}',
    '      res.sort(function(a,b){return b[0]-a[0]||a[1]-b[1];});',
    '      var seen={};res=res.filter(function(x){var k=x[2].u;if(seen[k])return false;seen[k]=1;return true;});',
    '      render(q,res.slice(0,50).map(function(x){return x[2];}));',
    '    });',
    '  }',
    '  go.addEventListener("click",run);',
    '  input.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();run();}});',
    '  var qs=null;',
    '  try{qs=new URLSearchParams(window.location.search).get("q");}catch(e){',
    '    var m=location.search.match(/[?&]q=([^&]*)/);if(m)qs=decodeURIComponent(m[1].replace(/\\+/g," "));}',
    '  if(qs){input.value=qs;}',
    '  run();',
]
script = " <script>\n(function(){\n  \"use strict\";\n" + "\n".join(JS_LINES) + "\n})();\n</script></body>"

# surgery on seg1: empty drawer for a universal page, random type channel
import re
seg1 = re.sub(r'(<div class="md-drawer-nav">).*?(</div> </aside>)', r"\1  \2", seg1, flags=re.S)
seg1 = seg1.replace('href="/random/?type=robot"', 'href="/random/?type=channel"')

# surgery on seg2: SEO footer + no active nav item
seg2 = seg2.replace(
    '<p class="footer-slogan">TGSOU 精心收录整理了',
    "<p class=\"footer-slogan\">TGSOU（tgsou.net）是专业的 TG中文搜索 平台，精心收录整理了",
)
seg2 = seg2.replace('class="footer-slogan">', 'class="footer-slogan">支持 TG搜 关键词直达，', 1)
seg2 = seg2.replace('<a href="/robot/" class="topbar-nav-item active">', '<a href="/robot/" class="topbar-nav-item ">')
seg2 = seg2.replace('<a href="/robot/" class="md-bottom-nav-item active">', '<a href="/robot/" class="md-bottom-nav-item ">')

body = seg1.replace("<!-- Main Workspace -->", main)
doc = new_head + " </head> " + body + " " + seg2 + script

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "search", "index.html")
open(out, "w", encoding="utf-8").write(doc)
print("written", os.path.getsize(out))
print("main tags:", doc.count("<main"), "closes:", doc.count("</main>"))
print("ldjson blocks:", doc.count("application/ld+json"))
print("h1 count:", doc.count("<h1"))
