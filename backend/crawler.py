"""
OPC 政策爬虫模块
自动抓取政府网站的OPC相关政策信息

使用方法：
  python crawler.py              # 运行一次完整爬取
  python crawler.py --source 广州  # 只爬取广州
  python crawler.py --extract URL  # 提取单个URL的政策信息
"""

import json
import hashlib
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# 配置
DATA_DIR = Path(__file__).parent.parent / 'data'
RESULTS_FILE = DATA_DIR / 'crawl_results.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}
TIMEOUT = 15

# ===== 抓取源配置 =====

SOURCES = [
    # 广东省 / 广州
    {"name": "广东省发改委", "url": "https://drc.gd.gov.cn/gkmlpt/", "keywords": ["OPC", "一人公司", "超级个体"]},
    {"name": "广州市政府公告", "url": "https://www.gz.gov.cn/zwgk/zdly/", "keywords": ["OPC", "一人公司", "人工智能"]},
    {"name": "海珠区政府", "url": "https://www.haizhu.gov.cn/gzhzrgzn/", "keywords": ["OPC", "人工智能", "场景", "征集"]},
    {"name": "黄埔区政府", "url": "http://www.hp.gov.cn/gkmlpt/", "keywords": ["OPC", "人工智能", "算力"]},
    {"name": "南沙区OPC", "url": "http://www.gzns.gov.cn/zwgk/rdzt/OPC/", "keywords": ["OPC", "一人公司"]},
    {"name": "番禺区政府", "url": "https://www.panyu.gov.cn/", "keywords": ["OPC", "创业"]},
    {"name": "白云区政府", "url": "https://www.by.gov.cn/", "keywords": ["OPC", "人工智能", "数据"]},
    # 深圳
    {"name": "深圳市工信局", "url": "https://gxj.sz.gov.cn/", "keywords": ["OPC", "一人公司", "AI创业"]},
    {"name": "深圳市发改委", "url": "https://fgw.sz.gov.cn/", "keywords": ["OPC", "人工智能"]},
    # 北京
    {"name": "北京市经信局", "url": "https://jxj.beijing.gov.cn/zwgk/", "keywords": ["OPC", "人工智能", "高精尖"]},
    {"name": "北京经开区", "url": "https://kfqgw.beijing.gov.cn/", "keywords": ["OPC", "模数", "AI"]},
    {"name": "海淀区科委", "url": "https://kw.beijing.gov.cn/", "keywords": ["OPC", "AI", "创新街区"]},
    # 上海
    {"name": "上海市经信委", "url": "https://jxj.sh.gov.cn/", "keywords": ["OPC", "超级创业者", "AI"]},
    {"name": "临港新片区", "url": "https://www.lingang.gov.cn/", "keywords": ["OPC", "超级个体", "288"]},
    # 杭州
    {"name": "杭州市经信局", "url": "https://jxj.hangzhou.gov.cn/", "keywords": ["OPC", "一人公司"]},
    {"name": "上城区政府", "url": "https://www.hzsc.gov.cn/", "keywords": ["OPC", "AI", "社区"]},
    # 武汉
    {"name": "武汉市政府", "url": "https://www.wuhan.gov.cn/zwgk/", "keywords": ["OPC", "一人公司", "AI"]},
    # 成都
    {"name": "成都市经信局", "url": "https://gk.chengdu.gov.cn/", "keywords": ["OPC", "一人公司", "AI"]},
    # 南京
    {"name": "南京市工信局", "url": "https://gxj.nanjing.gov.cn/", "keywords": ["OPC", "一人公司"]},
    # 合肥
    {"name": "合肥高新区", "url": "https://www.hefei.gov.cn/", "keywords": ["OPC", "AI模立方", "声谷"]},
]


def crawl_page(url):
    """抓取单个网页"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except Exception as e:
        print(f"  ✗ 抓取失败: {e}")
        return None


def extract_links(html, base_url, keywords):
    """从HTML中提取包含关键词的链接"""
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for link in soup.find_all('a', href=True):
        text = link.get_text(strip=True)
        if not text or len(text) < 4:
            continue

        if any(kw.lower() in text.lower() for kw in keywords):
            href = link['href']
            # 处理相对路径
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(base_url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                href = base_url.rstrip('/') + '/' + href

            results.append({
                'title': text[:100],
                'url': href,
                'url_hash': hashlib.md5(href.encode()).hexdigest()
            })

    return results


def extract_policy_info(url):
    """从政策页面提取结构化信息"""
    html = crawl_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    title = ''
    for tag in ['h1', 'h2', '.article-title', '.news-title', '#title']:
        el = soup.select_one(tag)
        if el:
            title = el.get_text(strip=True)
            break
    if not title:
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ''

    # 提取正文
    body = ''
    for sel in ['.article-content', '.news-content', '.TRS_Editor', '#zoom', '.content', 'article', '.main-content']:
        el = soup.select_one(sel)
        if el:
            body = el.get_text(separator='\n', strip=True)
            break
    if not body:
        body = soup.get_text(separator='\n', strip=True)[:5000]

    # 提取日期
    date_match = re.search(r'20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}', body[:500])
    publish_date = date_match.group().replace('年', '-').replace('月', '-').replace('/', '-') if date_match else ''

    # 提取金额关键信息
    amounts = re.findall(r'(?:最高|不超过|给予)?\s*(\d+(?:\.\d+)?)\s*万?元', body)
    keywords_found = []
    for kw in ['算力', '免租', '补贴', '奖励', '资助', 'OPC', '一人公司', '备案', '场景', '社区', '孵化']:
        if kw in body:
            keywords_found.append(kw)

    return {
        'title': title,
        'url': url,
        'publish_date': publish_date,
        'body_preview': body[:500],
        'amounts': amounts[:10],
        'keywords': keywords_found,
        'extracted_at': datetime.now().isoformat()
    }


def run_full_crawl(filter_source=None):
    """运行完整爬取"""
    print(f"\n{'='*50}")
    print(f"OPC 政策爬虫 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # 加载已有结果
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            all_results = json.load(f)
    else:
        all_results = {'results': [], 'last_crawl': ''}

    existing_hashes = {r['url_hash'] for r in all_results['results']}
    new_count = 0

    sources = SOURCES
    if filter_source:
        sources = [s for s in SOURCES if filter_source in s['name']]

    for source in sources:
        print(f"▶ 正在爬取: {source['name']} ({source['url']})")

        html = crawl_page(source['url'])
        links = extract_links(html, source['url'], source['keywords'])

        for link in links:
            if link['url_hash'] not in existing_hashes:
                link['source'] = source['name']
                link['found_at'] = datetime.now().isoformat()
                link['status'] = 'new'
                all_results['results'].append(link)
                existing_hashes.add(link['url_hash'])
                new_count += 1
                print(f"  ✓ 新发现: {link['title'][:60]}")

        print(f"  共找到 {len(links)} 个链接")
        time.sleep(1)  # 礼貌爬取

    all_results['last_crawl'] = datetime.now().isoformat()

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"爬取完成! 新发现 {new_count} 个链接")
    print(f"累计 {len(all_results['results'])} 个结果")
    print(f"结果保存至: {RESULTS_FILE}")
    print(f"{'='*50}\n")

    return all_results


if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--extract' and len(sys.argv) > 2:
            info = extract_policy_info(sys.argv[2])
            if info:
                print(json.dumps(info, ensure_ascii=False, indent=2))
        elif sys.argv[1] == '--source' and len(sys.argv) > 2:
            run_full_crawl(sys.argv[2])
        else:
            print("用法: python crawler.py [--source 城市名] [--extract URL]")
    else:
        run_full_crawl()
