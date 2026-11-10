#!/usr/bin/env python3
"""热榜日报 Logo 素材生成：圆角方块（--accent 浅色组 #8f5e2e）+「热」衬线粗体（--bg 奶油 #fbf9f4）。
配色实读自 template.html：深色组 --accent:#d9a94c / --bg:#0f1114；浅色组 --accent:#8f5e2e / --bg:#fbf9f4。
规格定版取浅色组（字色为「--bg 的奶油色」）。字体一律 Noto CJK .ttc index=2（简体字面）。"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'assets')
os.makedirs(OUT, exist_ok=True)

ACCENT = (0x8F, 0x5E, 0x2E)      # --accent (light)
CREAM = (0xFB, 0xF9, 0xF4)       # --bg (light) 奶油色
TEXT = (0x1A, 0x1A, 0x1A)        # --text (light)
MUTED = (0x5F, 0x5F, 0x5F)       # --muted (light)

SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SANS_B = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
SANS_R = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
IDX = 2  # 简体字面，禁止省略


def fit_font(path, text, target_h=None, target_w=None, start=400):
    size = start
    probe = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    while size > 8:
        f = ImageFont.truetype(path, size, index=IDX)
        b = probe.textbbox((0, 0), text, font=f)
        w, h = b[2] - b[0], b[3] - b[1]
        if target_h and h > target_h:
            size = int(size * target_h / h) - 1
            continue
        if target_w and w > target_w:
            size = int(size * target_w / w) - 1
            continue
        return f, b
    return f, b


def draw_mark(size, bleed=False):
    """圆角方块 + 热 字（字高约占画布 62%），4x 超采样。bleed=True 时满幅方块（apple icon）。"""
    ss = 4
    S = size * ss
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bleed:
        d.rectangle([0, 0, S - 1, S - 1], fill=ACCENT + (255,))
    else:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.23), fill=ACCENT + (255,))
    font, b = fit_font(SERIF, '热', target_h=int(S * 0.62), start=S)
    x = (S - (b[2] - b[0])) / 2 - b[0]
    y = (S - (b[3] - b[1])) / 2 - b[1]
    d.text((x, y), '热', font=font, fill=CREAM + (255,))
    return img.resize((size, size), Image.LANCZOS)


def main():
    master = draw_mark(512)
    master.save(os.path.join(OUT, 'logo.png'))
    master.save(os.path.join(OUT, 'favicon.ico'), format='ICO',
                sizes=[(16, 16), (32, 32), (48, 48)])
    draw_mark(32).save(os.path.join(OUT, 'favicon-32.png'))
    draw_mark(180, bleed=True).convert('RGB').save(os.path.join(OUT, 'apple-touch-icon.png'))

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
           '<rect width="100" height="100" rx="23" fill="#8f5e2e"/>'
           '<text x="50" y="54" font-family="Noto Serif SC, serif" font-size="58" '
           'font-weight="700" fill="#fbf9f4" text-anchor="middle" '
           'dominant-baseline="central">热</text></svg>')
    for name in ('favicon.svg', 'logo.svg'):
        open(os.path.join(OUT, name), 'w', encoding='utf-8').write(svg)

    # ---- og-image 1200x630，2x 超采样 ----
    ss = 2
    W, H = 1200 * ss, 630 * ss
    og = Image.new('RGB', (W, H), CREAM)
    mark = draw_mark(300 * ss)
    mx, my = 100 * ss, (H - 300 * ss) // 2
    og.paste(mark, (mx, my), mark)
    d = ImageDraw.Draw(og)
    tx = (100 + 300 + 72) * ss
    max_w = W - tx - 80 * ss
    f_title, bt = fit_font(SERIF, '热榜日报', target_w=max_w, start=150 * ss)
    f_sub, bs = fit_font(SANS_R, '每日热榜汇总 · 10 站热榜聚合', target_w=max_w, start=44 * ss)
    f_dom, bd = fit_font(SANS_R, 'hot.jinzhai.icu', target_w=max_w, start=32 * ss)
    th, sh, dh = bt[3] - bt[1], bs[3] - bs[1], bd[3] - bd[1]
    gap1, gap2 = 34 * ss, 26 * ss
    total = th + gap1 + sh + gap2 + dh
    y = (H - total) // 2
    d.text((tx - bt[0], y - bt[1]), '热榜日报', font=f_title, fill=TEXT)
    y += th + gap1
    d.text((tx - bs[0], y - bs[1]), '每日热榜汇总 · 10 站热榜聚合', font=f_sub, fill=MUTED)
    y += sh + gap2
    d.text((tx - bd[0], y - bd[1]), 'hot.jinzhai.icu', font=f_dom, fill=ACCENT)
    for txt, f in (('热榜日报', f_title), ('每日热榜汇总 · 10 站热榜聚合', f_sub), ('hot.jinzhai.icu', f_dom)):
        b = d.textbbox((0, 0), txt, font=f)
        assert tx + (b[2] - b[0]) <= W - 40 * ss, f'og text overflow: {txt}'
    og = og.resize((1200, 630), Image.LANCZOS)
    og.save(os.path.join(OUT, 'og-image.png'))

    # ---- 自检 ----
    for name in ('logo.png', 'favicon.ico', 'favicon-32.png', 'apple-touch-icon.png',
                 'og-image.png', 'favicon.svg', 'logo.svg'):
        p = os.path.join(OUT, name)
        size = os.path.getsize(p)
        if name.endswith(('.png', '.ico')):
            im = Image.open(p)
            extra = f'{im.size} {im.mode}' + (f' ico_sizes={sorted(im.info.get("sizes", []))}' if name.endswith('.ico') else '')
            print(f'{name}: {size}B {extra}')
        else:
            print(f'{name}: {size}B (svg)')


if __name__ == '__main__':
    main()
