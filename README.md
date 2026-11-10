# daily-hot-digest · 热榜日报

![热榜日报](assets/og-image.png)

一句话定位：把 10 个中文热榜站点聚合进一个单文件静态页面，每天自动刷新——打开就是今天的全网热点。

线上演示：<https://hot.jinzhai.icu>

## 特性

- **单文件、零外部请求**：整页只有一个 `index.html`，榜单数据在构建时内嵌进页面，运行时不请求任何外部接口，可离线打开、可整页保存。
- **10 源聚合**：微博、百度、今日头条、知乎、哔哩哔哩、抖音、GitHub、Hacker News、掘金、财联社，按「热搜综合 / 深度讨论 / 视频 / 科技 / 财经」五组呈现，每源 Top 10。
- **每日自动刷新**：构建脚本拉取最新榜单并重新注入模板，配合任意定时器（cron / GitHub Actions 等）即可无人值守更新；成功源少于 7 个时自动中止，保留上一次产物，不发残页。
- **导航与滚动高亮**：分组导航吸附顶部，滚动时自动高亮当前分组，点击锚点落点不被顶栏遮挡（已按实测顶栏高度校准滚动边距）。
- **SEO 基础件齐全**：canonical、Open Graph / Twitter 分享卡、WebSite JSON-LD 随页面内置；`robots.txt`、`sitemap.xml`（lastmod 随构建日期）、`llms.txt` 由构建脚本每次一并生成。
- **Logo 套件**：「热」字标已备齐 favicon（ico / svg / 32px PNG）、apple-touch-icon、logo（svg / png）与 1200×630 分享图，生成脚本在 `make_assets.py`。
- **深浅双色**：跟随系统 `prefers-color-scheme`，深色墨黑 + 金、浅色奶油 + 金棕，两套配色各自校准。

## 架构

```text
DailyHotApi 兼容接口 (GET /hot-lists/<source>)
        │  build.py 逐源并发拉取 10 个源，组装 DATA 文档
        ▼
template.html ── 大括号配平替换 const DATA ──► dist/index.html（单文件）
        │  同轮生成 robots.txt / sitemap.xml / llms.txt + 拷贝 Logo 素材
        ▼
静态托管（线上用 Cloudflare Pages，任何静态托管均可）
```

页面本身不含任何后端代码；数据只在构建期流动，运行期零请求。

## 快速开始

前置：先有一个 DailyHotApi 兼容接口在跑（见下方致谢的上游项目），或使用任意已部署的兼容实例。

```bash
# 1) 构建（默认连 http://127.0.0.1:6689 的本地实例）
python3 build.py

# 指向其他实例：
DAILY_HOT_API_BASE=https://your-instance.example python3 build.py

# 2) 预览：直接打开 dist/index.html，或起个静态服务器
python3 -m http.server -d dist 8000

# 3) 可选：部署到 Cloudflare Pages（需先 npx wrangler login）
python3 build.py --deploy
```

每日自动刷新示例（cron）：

```cron
45 8 * * *  cd /path/to/daily-hot-digest && python3 build.py --deploy
```

Logo 素材如需重做（改配色 / 字标后）：`python3 make_assets.py`（依赖 Pillow 与 Noto CJK 字体，素材输出到 `assets/`）。

## 数据契约

构建时注入模板的 `DATA` 文档结构：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `generated_at` | string | 生成时间，ISO 8601（UTC+8），如 `2026-11-10T09:35:49+08:00` |
| `sources` | array | 固定 10 个源，顺序与接口拉取清单一致 |
| `sources[].name` | string | 源标识：`weibo` / `baidu` / `toutiao` / `zhihu` / `bilibili` / `douyin` / `github` / `hackernews` / `cls` / `juejin` |
| `sources[].title` | string | 源展示名（如「微博」） |
| `sources[].type` | string | 榜单类型（如「热搜榜」） |
| `sources[].total` | number | 该源榜单总条数；`0` 表示本次拉取失败 |
| `sources[].items` | array | 条目数组（构建取前 15 条，页面展示 Top 10） |
| `sources[].items[].rank` | number | 排名，从 1 起 |
| `sources[].items[].title` | string | 条目标题 |
| `sources[].items[].hot` | number \| string \| null | 热度值（各源口径不一，可能为格式化字符串或空） |
| `sources[].items[].url` | string | 条目原文链接（指向原平台） |

仓库内的 `template.html` 内嵌的是一份演示样本数据（3 个源 × 3 条，取自线上某日真实榜单），构建后会被实时数据整段替换。

## 致谢

- 数据接口兼容 [imsyy/DailyHotApi](https://github.com/imsyy/DailyHotApi)，本项目只消费其 `GET /hot-lists/<source>` 接口，不含其代码。
- 各榜单数据与条目标题、链接的权利归各原平台所有，本项目仅做聚合展示与跳转。

## English (brief)

**daily-hot-digest** aggregates Top-10 lists from 10 Chinese trending sources (Weibo, Baidu, Toutiao, Zhihu, Bilibili, Douyin, GitHub, Hacker News, Juejin, CLS) into a single self-contained static page — no runtime requests, rebuilt daily by `build.py` from any DailyHotApi-compatible endpoint (`DAILY_HOT_API_BASE`). SEO basics (canonical, Open Graph, sitemap, llms.txt, JSON-LD) and a full logo kit are generated with every build. Live demo: <https://hot.jinzhai.icu>. MIT licensed.

## License

[MIT](LICENSE) © 2026 Ding Xiang
