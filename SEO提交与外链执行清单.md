# opcgate.com SEO提交与外链执行清单

更新日期：2026-04-16

适用站点：
- `https://opcgate.com/`
- `https://opcgate.com/sitemap.xml`
- `https://opcgate.com/compare`
- `https://opcgate.com/seo/index`
- `https://opcgate.com/seo/cities/index`

## 当前状态

今天已完成：
- 线上重新部署
- `sitemap.xml` 扩充到 `60` 个 URL
- 新增 `35` 个静态城市页
- 重点城市页示例：`https://opcgate.com/seo/cities/深圳`

现在最该做的，不是继续堆页面，而是让三家搜索引擎尽快重新抓你这批新页。

## 一、Google Search Console 提交清单

目标：
- 让 Google 尽快发现新 `sitemap`
- 让首页、对比页、城市页尽快进入抓取队列

执行顺序：
1. 打开 [Add a website property to Search Console](https://support.google.com/webmasters/answer/34592)。
2. 优先添加 `Domain property`：`opcgate.com`。
3. 如果你暂时不方便改 DNS，再退而求其次加 `URL-prefix property`：`https://opcgate.com/`。
4. 验证成功后，打开 [Sitemaps report](https://support.google.com/webmasters/answer/7451001)。
5. 提交：`https://opcgate.com/sitemap.xml`。
6. 打开 [URL Inspection tool](https://support.google.com/webmasters/answer/9012289)，手动请求以下页面抓取：
   - `https://opcgate.com/`
   - `https://opcgate.com/compare`
   - `https://opcgate.com/seo/index`
   - `https://opcgate.com/seo/cities/index`
   - `https://opcgate.com/seo/cities/深圳`
   - `https://opcgate.com/seo/cities/北京`
   - `https://opcgate.com/seo/cities/上海`
   - `https://opcgate.com/seo/cities/杭州`
   - `https://opcgate.com/guangzhou`
   - `https://opcgate.com/suzhou`
7. 3 到 7 天后回看：
   - Page indexing
   - Performance
   - URL Inspection

注意：
- Google 官方明确建议，多页面更新时优先交 `sitemap`，不是一条条狂点 `Request indexing`。
- `Request indexing` 有每日额度，留给首页、对比页、最重要城市页。

## 二、Bing Webmaster Tools 提交清单

目标：
- 让 Bing 先吃下新 `sitemap`
- 后续用 IndexNow 加快新增页发现

执行顺序：
1. 打开 [Bing Webmaster Tools](https://www.bing.com/webmasters/about)。
2. 添加并验证 `opcgate.com`。
3. 在站点后台提交：`https://opcgate.com/sitemap.xml`。
4. 重点开启或接入 [IndexNow Get Started](https://www.bing.com/indexnow/IndexNowView/IndexNowGetStartedView)。
5. 以后每次你新增或大改页面时，再把更新页推给 IndexNow。

为什么推荐做：
- Bing 官方现在主推 [Why IndexNow](https://www.bing.com/webmasters/url-submission-api)。
- 对你这种“新增城市页、对比页、政策页”的站，IndexNow 比等自然发现更合适。

我对你站的建议：
- Bing 不要只交首页。
- 先交 `sitemap`，再把重点新页走一遍 IndexNow。
- 第一批建议推送：
  - 首页
  - `compare`
  - `seo/index`
  - `seo/cities/index`
  - 新增的 35 个城市页

说明：
- Bing 的部分帮助页在当前环境里是 JS 渲染，我能确认官方入口和 IndexNow 文档，但具体后台按钮文案可能以你登录后实际页面为准。

## 三、百度搜索资源平台 提交清单

目标：
- 先把站点纳入资源平台
- 再用“链接提交”把历史页和新增页分开处理

执行顺序：
1. 登录百度搜索资源平台，先完成站点验证。
   - 这是根据平台工具流程做的推断；我没拿到一篇当前可直接打开的验证帮助页，但资源平台工具都以“已验证站点”为前提。
2. 进入链接提交工具。
3. 用 `sitemap` 提交历史页和重要页。
4. 对新增高质量页面，优先用主动推送。
5. 如果你拿到了“快速抓取”资格，再把高优先级新页放进去。
6. 后续每天看一次 [索引量工具](https://ziyuan.baidu.com/indexs/)。

怎么分工最合理：
- `sitemap`：交全站历史页、重点页、稳定更新页。
- 主动推送：交当天新增或大改的高质量页面。
- 手动提交：补漏。
- 快速抓取：给你最重要、最想快收录的页面。

平台依据：
- 百度在 [sitemap工具升级改名公告](https://ziyuan.baidu.com/wiki/560) 里把 sitemap、实时推送、手动提交合并进“链接提交”，并明确说明：
  - 主动推送最快
  - sitemap 适合历史数据和重要数据
  - 手动提交适合补漏
- 百度在 `2024-04-24` 的 [关于升级平台「快速收录」工具的通知](https://ziyuan.baidu.com/wiki/3546) 里说明：`快速收录` 已升级为 `快速抓取`。
- 百度在 [链接提交主动推送产品升级公告](https://ziyuan.baidu.com/wiki/872) 里提到主动推送不再限制每天提交数量，但反复提交历史链接、低质链接可能被降权或限制。

我对你站的建议：
- 百度最先提交这批：
  - 首页
  - `compare`
  - `seo/index`
  - `seo/cities/index`
  - `seo/cities/深圳`
  - `seo/cities/北京`
  - `seo/cities/上海`
  - `seo/cities/杭州`
  - `guangzhou`
  - `suzhou`
- 以后新增城市页时：
  - 当天主动推送
  - 第二天确认进 sitemap

## 四、最有效的外链执行表

原则：
- 不买垃圾外链
- 不做站群目录
- 不只链首页
- 优先给“高意图深页”做外链

### 第一批外链优先级

| 优先级 | 渠道 | 发什么 | 链到哪里 | 锚文本建议 | 目标 |
| --- | --- | --- | --- | --- | --- |
| P1 | 你自己的 GitHub README / Repo 描述 | 产品说明、数据来源、维护日志 | 首页、维护日志、对比页 | `opcgate`、`OPC 选址决策工具` | 品牌实体和基础信任 |
| P1 | 公众号 / 个人博客 | 城市对比长文 | 对应 `seo/*.html` | `广州 vs 深圳 vs 苏州 OPC 对比` | 高意图关键词 |
| P1 | 知乎回答 | 回答“哪个城市适合做 OPC / 一人公司” | 对比页、城市页 | 自然句式，不要生硬关键词 | 搜索长尾流量 |
| P1 | 朋友圈 / 微信社群 / 创业群 | 情报更新帖 | 首页、城市页 | 直接 URL 或品牌名 | 第一批真实点击 |
| P2 | 行业导航 / 工具导航站 | 站点收录 | 首页 | 品牌词 + URL | 基础外链池 |
| P2 | AI 创业 / 孵化器 / 园区相关文章 | 竞品整理、资源对比 | 城市页、社区页 | `深圳 OPC 政策汇总` 这类自然锚文本 | 垂直相关信号 |
| P2 | 合作方官网 / 朋友博客 | 推荐资源页 | 首页或一个最强深页 | 裸链或品牌词 | 相关性外链 |
| P3 | 新闻稿 / 媒体软文 | 明确事件或数据发布 | 维护日志、年度榜单页 | 品牌词 | 品牌背书，不是主力 |

### 外链内容怎么发最有效

不要发：
- “欢迎访问我的网站”
- “这是一个很好用的工具”
- 纯广告文

要发：
- 对比型内容：`广州 vs 深圳 vs 苏州，做 OPC 到底去哪`
- 决策型内容：`哪些城市适合 AI 语音创业，哪些不适合`
- 情报型内容：`2026 年 OPC 政策更新最密集的 10 个城市`
- 核验型内容：`我把 35 个城市页和官方来源整理成了一个数据库`

### 深页外链分配

不要把 10 条外链都打给首页。

建议分配：
- 40% 给首页
- 30% 给 `compare`
- 20% 给热门对比页
- 10% 给重点城市页

对你现在这站，最值得吃外链的深页是：
- `https://opcgate.com/compare`
- `https://opcgate.com/seo/guangzhou-vs-shenzhen-vs-suzhou`
- `https://opcgate.com/seo/beijing-vs-shanghai-vs-shenzhen`
- `https://opcgate.com/seo/cities/深圳`
- `https://opcgate.com/seo/cities/北京`
- `https://opcgate.com/seo/cities/index`

## 五、30 天执行节奏

### 第 1 周
- 提交 Google Search Console
- 提交 Bing Webmaster Tools
- 提交百度搜索资源平台
- 手动请求最重要的 10 个页面

### 第 2 周
- 发 2 篇公众号或博客文章
- 发 3 条知乎回答
- GitHub README 加站点入口

### 第 3 周
- 发 1 篇“城市对比榜单”长文
- 争取 3 到 5 个相关站点或朋友博客自然引用
- 继续提交新增页到百度和 Bing

### 第 4 周
- 看三家平台的抓取、收录、展现变化
- 根据收录情况补强：
  - 被抓但不收录：补内容和内链
  - 没抓到：补提交和外链
  - 收录慢：补主动推送和高点击入口

## 六、别做的事

- 不买批量垃圾外链
- 不做论坛签名、站群评论、隐藏页跳转
- 不把同一批历史页反复主动推送给百度
- 不用一堆完全一致的关键词锚文本
- 不把首页当成唯一落地页

## 七、我建议你下一步继续做的 3 件事

1. 先完成三家平台提交通道。
2. 同步把 GitHub README、公众号文章、知乎回答发出去，先拿第一批自然外链。
3. 下一轮我直接给你做 `IndexNow 接入`，以及一版 `GitHub README SEO 化改写`。

## 参考来源

Google 官方：
- [Add a website property to Search Console](https://support.google.com/webmasters/answer/34592)
- [Sitemaps report](https://support.google.com/webmasters/answer/7451001)
- [URL Inspection tool](https://support.google.com/webmasters/answer/9012289)
- [Get started with Search Console](https://support.google.com/webmasters/answer/9128669)

Bing 官方：
- [Bing Webmaster Tools](https://www.bing.com/webmasters/about)
- [Why IndexNow](https://www.bing.com/webmasters/url-submission-api)
- [How to add IndexNow to your website](https://www.bing.com/indexnow/IndexNowView/IndexNowGetStartedView)
- [Bing sitemap help page](https://www.bing.com/webmasters/help/how-to-submit-sitemaps-82a15bd4)

百度官方：
- [sitemap工具升级改名公告](https://ziyuan.baidu.com/wiki/560)
- [关于升级平台「快速收录」工具的通知](https://ziyuan.baidu.com/wiki/3546)
- [链接提交主动推送产品升级公告](https://ziyuan.baidu.com/wiki/872)
- [索引量工具](https://ziyuan.baidu.com/indexs/)
