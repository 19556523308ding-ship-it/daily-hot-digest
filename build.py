#!/usr/bin/env python3
"""daily-hot-digest 每日热榜汇总页构建脚本。

从 DailyHotApi 兼容接口逐源拉取榜单 -> 替换模板中的 const DATA -> 生成 dist/。
用法:
  python3 build.py            只构建（数据接口地址见环境变量 DAILY_HOT_API_BASE，
                              默认 http://127.0.0.1:6689，即本地 DailyHotApi 实例）
  python3 build.py --deploy   构建后用 wrangler 部署到 Cloudflare Pages
                              （项目名 daily-digest，需先自行登录 wrangler）
成功拉到数据的源少于 7 个时中止构建，保留上一次产物。
"""
import concurrent.futures
import datetime
import json
import os
import shutil
import subprocess
import sys
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
API_BASE = os.environ.get('DAILY_HOT_API_BASE', 'http://127.0.0.1:6689').rstrip('/')
PROJECT = 'daily-digest'
SOURCES = ['weibo', 'baidu', 'toutiao', 'zhihu', 'bilibili',
           'douyin', 'github', 'hackernews', 'cls', 'juejin']


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def fetch(source):
    """拉单个源：GET {API_BASE}/hot-lists/<source>，与 DailyHotApi 返回结构对齐。"""
    try:
        req = urllib.request.Request(f'{API_BASE}/hot-lists/{source}',
                                     headers={'Connection': 'close'})
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.load(r)
        items = [{'rank': i + 1, 'title': it.get('title'),
                  'hot': (it.get('hot') or None), 'url': it.get('url')}
                 for i, it in enumerate((d.get('data') or [])[:15])]
        return source, {'name': source, 'title': d.get('title'),
                        'type': d.get('type'), 'total': d.get('total'),
                        'items': items}
    except Exception as e:
        return source, {'name': source, 'title': source, 'total': 0,
                        'items': [], 'error': str(e)[:80]}


def fetch_all():
    out = {}
    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        for s, res in ex.map(fetch, SOURCES):
            out[s] = res
    tz8 = datetime.timezone(datetime.timedelta(hours=8))
    doc = {'generated_at': datetime.datetime.now(tz8).isoformat(timespec='seconds'),
           'sources': [out[s] for s in SOURCES]}
    ok = sum(1 for s in doc['sources'] if s.get('total', 0) > 0)
    items = sum(len(s.get('items', [])) for s in doc['sources'])
    print(f'digest ok: {ok}/{len(SOURCES)} sources, at {doc["generated_at"]}')
    print(f'data: {ok}/{len(doc["sources"])} sources ok, {items} items, at {doc["generated_at"]}')
    return doc, ok


def main():
    doc, ok = fetch_all()
    if ok < 7:
        print('ABORT: too few sources, keep previous build')
        sys.exit(1)

    tpl = open(os.path.join(BASE, 'template.html'), encoding='utf-8').read()
    i = tpl.find('const DATA = ')
    start = tpl.find('{', i)
    depth, end = 0, None
    for j in range(start, len(tpl)):
        if tpl[j] == '{':
            depth += 1
        elif tpl[j] == '}':
            depth -= 1
            if depth == 0:
                end = j
                break
    data_js = json.dumps(doc, ensure_ascii=False).replace('</', '<\\/')
    html = tpl[:start] + data_js + tpl[end + 1:]
    html = html.replace('页面数据取自 <span class="mono" id="dataFile">digest.json</span>，无外部请求，可在本地直接打开。',
                        '页面数据每日自动汇总生成，本页为单文件、零外部请求。')
    dist = os.path.join(BASE, 'dist')
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, 'index.html')
    open(out, 'w', encoding='utf-8').write(html)
    print(f'built: {out} ({len(html)} bytes)')

    # ---- SEO 基础文件（robots / sitemap / llms）与 Logo 素材，随页一并部署 ----
    open(os.path.join(dist, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\n\nSitemap: https://hot.jinzhai.icu/sitemap.xml\n')
    lastmod = str(doc['generated_at'])[:10]
    open(os.path.join(dist, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'<url><loc>https://hot.jinzhai.icu/</loc><lastmod>{lastmod}</lastmod>'
        '<changefreq>daily</changefreq></url>\n</urlset>\n')
    open(os.path.join(dist, 'llms.txt'), 'w', encoding='utf-8').write(
        '# 热榜日报\n\n'
        '> 每日聚合 10 个中文热榜站点的单页日报。\n\n'
        '- 站点：热榜日报（每日热榜汇总）\n'
        '- 域名：https://hot.jinzhai.icu/\n'
        '- 更新节奏：每日约 08:45（Asia/Shanghai）自动更新当日榜单\n\n'
        '## 分组与来源\n\n'
        '- 热搜综合：微博、百度、今日头条\n'
        '- 深度讨论：知乎\n'
        '- 视频：哔哩哔哩、抖音\n'
        '- 科技：GitHub、Hacker News、掘金\n'
        '- 财经：财联社\n\n'
        '## 主页面\n\n'
        '- [每日热榜汇总](https://hot.jinzhai.icu/)：全部 10 站当日热榜（每站 Top 10）\n')
    assets = os.path.join(BASE, 'assets')
    for name in ('favicon.ico', 'favicon.svg', 'favicon-32.png',
                 'apple-touch-icon.png', 'logo.png', 'logo.svg', 'og-image.png'):
        src = os.path.join(assets, name)
        if not os.path.isfile(src):
            raise FileNotFoundError(f'asset missing, run make_assets.py first: {src}')
        shutil.copy(src, os.path.join(dist, name))
    print('seo files + assets copied to dist')

    if '--deploy' in sys.argv:
        r = sh(['npx', 'wrangler', 'pages', 'deploy', dist,
                '--project-name', PROJECT])
        print(r.stdout[-1200:])
        print(r.stderr[-400:])
        if r.returncode != 0:
            sys.exit(r.returncode)


if __name__ == '__main__':
    main()
