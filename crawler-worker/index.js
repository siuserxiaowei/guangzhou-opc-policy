/**
 * OPC 政策爬虫 — Cloudflare Worker (Cron Trigger)
 * 每12小时自动扫描政府网站，发现新OPC政策
 */

const SOURCES = [
  // 广东
  { name: '广州市政府', url: 'https://www.gz.gov.cn/zwgk/zdly/', keywords: ['OPC', '一人公司', '超级个体'] },
  { name: '海珠区政府', url: 'https://www.haizhu.gov.cn/gzhzrgzn/', keywords: ['OPC', '人工智能', '场景'] },
  { name: '越秀区政府', url: 'http://www.yuexiu.gov.cn/yxdt/yxkx/', keywords: ['OPC', '一人公司', '人工智能', 'AI'] },
  { name: '深圳市政府', url: 'https://www.sz.gov.cn/cn/xxgk/zfxxgj/tzgg/', keywords: ['OPC', '一人公司', 'AI创业'] },
  { name: '东莞市政府', url: 'https://www.dg.gov.cn/zwgk/', keywords: ['OPC', '一人公司'] },
  // 长三角
  { name: '苏州市政府', url: 'https://www.suzhou.gov.cn/szsrmzf/szyw/', keywords: ['OPC', '一人公司'] },
  { name: '杭州市政府', url: 'https://www.hangzhou.gov.cn/', keywords: ['OPC', '一人公司'] },
  { name: '上海市经信委', url: 'https://jxj.sh.gov.cn/', keywords: ['OPC', '超级创业者'] },
  { name: '南京市政府', url: 'https://www.nanjing.gov.cn/', keywords: ['OPC', '一人公司'] },
  // 北方
  { name: '北京市经信局', url: 'https://jxj.beijing.gov.cn/zwgk/', keywords: ['OPC', '人工智能', '模数'] },
  { name: '青岛市政府', url: 'http://gxj.qingdao.gov.cn/', keywords: ['OPC', '一人公司'] },
  { name: '济南市政府', url: 'https://www.jinan.gov.cn/', keywords: ['OPC', '数智'] },
  // 中西部
  { name: '武汉市政府', url: 'https://www.wuhan.gov.cn/zwgk/', keywords: ['OPC', '一人公司'] },
  { name: '成都市政府', url: 'https://www.chengdu.gov.cn/', keywords: ['OPC', '一人公司'] },
  // 惠州(重点监控)
  { name: '惠州市政府', url: 'https://www.huizhou.gov.cn/', keywords: ['OPC', '一人公司', '人工智能'] },
  { name: '惠阳区政府', url: 'http://www.huiyang.gov.cn/', keywords: ['OPC', '一人公司', 'AI'] },
];

async function crawlSource(source) {
  try {
    const resp = await fetch(source.url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; OPCBot/1.0; +https://opcgate.com)' },
      signal: AbortSignal.timeout(10000),
    });
    if (!resp.ok) return { source: source.name, status: 'error', code: resp.status, links: [] };

    const html = await resp.text();
    const links = [];

    // Simple regex to find links with keywords
    const linkRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>([^<]+)<\/a>/gi;
    let match;
    while ((match = linkRegex.exec(html)) !== null) {
      const href = match[1];
      const text = match[2].trim();
      if (text.length < 4) continue;
      if (source.keywords.some(kw => text.includes(kw))) {
        let fullUrl = href;
        if (href.startsWith('/')) {
          const u = new URL(source.url);
          fullUrl = `${u.protocol}//${u.host}${href}`;
        } else if (!href.startsWith('http')) {
          fullUrl = source.url.replace(/\/$/, '') + '/' + href;
        }
        links.push({ title: text.substring(0, 100), url: fullUrl });
      }
    }

    return { source: source.name, status: 'ok', links };
  } catch (e) {
    return { source: source.name, status: 'error', message: e.message, links: [] };
  }
}

async function runCrawl(env) {
  const timestamp = new Date().toISOString();
  console.log(`[OPC Crawler] Starting at ${timestamp}`);

  // Load existing results from KV
  let existing = {};
  try {
    const data = await env.OPC_DATA.get('crawl_results', 'json');
    if (data) existing = data;
  } catch (e) {}

  const seenUrls = new Set(Object.keys(existing.urls || {}));
  const newFinds = [];

  // Crawl all sources concurrently (batches of 4)
  for (let i = 0; i < SOURCES.length; i += 4) {
    const batch = SOURCES.slice(i, i + 4);
    const results = await Promise.all(batch.map(s => crawlSource(s)));

    for (const result of results) {
      for (const link of result.links) {
        if (!seenUrls.has(link.url)) {
          seenUrls.add(link.url);
          newFinds.push({
            ...link,
            source: result.source,
            found_at: timestamp,
          });
        }
      }
    }
  }

  // Save to KV
  const urls = existing.urls || {};
  for (const find of newFinds) {
    urls[find.url] = find;
  }

  const crawlData = {
    urls,
    last_crawl: timestamp,
    total_urls: Object.keys(urls).length,
    history: [
      ...(existing.history || []).slice(-100),
      { timestamp, new_count: newFinds.length, sources_checked: SOURCES.length }
    ]
  };

  await env.OPC_DATA.put('crawl_results', JSON.stringify(crawlData));
  await env.OPC_DATA.put('last_crawl_time', timestamp);
  await env.OPC_DATA.put('new_finds_latest', JSON.stringify(newFinds));

  console.log(`[OPC Crawler] Done. Found ${newFinds.length} new links. Total: ${crawlData.total_urls}`);

  return { new_count: newFinds.length, total: crawlData.total_urls, timestamp };
}

export default {
  // Cron trigger - runs every 12 hours
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runCrawl(env));
  },

  // HTTP handler - manual trigger + status API
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS headers
    const headers = {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    };

    // GET /status - crawler status
    if (url.pathname === '/status' || url.pathname === '/') {
      const lastCrawl = await env.OPC_DATA.get('last_crawl_time');
      const data = await env.OPC_DATA.get('crawl_results', 'json');
      return new Response(JSON.stringify({
        status: 'running',
        last_crawl: lastCrawl || 'never',
        total_urls: data?.total_urls || 0,
        sources: SOURCES.length,
        schedule: 'every 12 hours',
        history: (data?.history || []).slice(-10),
      }), { headers });
    }

    // GET /new - latest new findings
    if (url.pathname === '/new') {
      const finds = await env.OPC_DATA.get('new_finds_latest', 'json');
      return new Response(JSON.stringify({ finds: finds || [] }), { headers });
    }

    // POST /crawl - manual trigger
    if (url.pathname === '/crawl' && request.method === 'POST') {
      const result = await runCrawl(env);
      return new Response(JSON.stringify(result), { headers });
    }

    return new Response(JSON.stringify({ error: 'Not found', endpoints: ['/', '/status', '/new', 'POST /crawl'] }), { status: 404, headers });
  },
};
