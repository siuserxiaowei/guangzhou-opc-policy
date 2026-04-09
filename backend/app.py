"""
OPC 全国政策导航 — 后端服务
功能：
1. 自动爬虫抓取政策
2. AI 政策顾问（Anthropic Claude）
3. 政策变动追踪
4. 申报日历与提醒
5. 数据看板 API
"""

import json
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../')
CORS(app)

DATA_DIR = Path(__file__).parent.parent / 'data'
POLICIES_FILE = DATA_DIR / 'policies.json'
CHANGES_FILE = DATA_DIR / 'changes.json'
SUBSCRIBERS_FILE = DATA_DIR / 'subscribers.json'

# ============================================================
# 1. DATA LAYER
# ============================================================

def load_policies():
    with open(POLICIES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_policies(data):
    with open(POLICIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_changes():
    if CHANGES_FILE.exists():
        with open(CHANGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"changes": []}

def save_changes(data):
    with open(CHANGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_subscribers():
    if SUBSCRIBERS_FILE.exists():
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"subscribers": []}

def save_subscribers(data):
    with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 2. CRAWLER — 自动爬取政策
# ============================================================

# Government sites to monitor
CRAWL_SOURCES = [
    {"name": "广东省发改委", "url": "https://drc.gd.gov.cn/", "keywords": ["OPC", "一人公司", "超级个体", "人工智能"]},
    {"name": "广州市政府", "url": "https://www.gz.gov.cn/", "keywords": ["OPC", "一人公司", "创业"]},
    {"name": "海珠区政府", "url": "https://www.haizhu.gov.cn/", "keywords": ["OPC", "人工智能", "场景"]},
    {"name": "深圳市政府", "url": "https://www.sz.gov.cn/", "keywords": ["OPC", "一人公司", "AI创业"]},
    {"name": "北京市经信局", "url": "https://jxj.beijing.gov.cn/", "keywords": ["OPC", "人工智能", "高精尖"]},
    {"name": "上海市经信委", "url": "https://www.shanghai.gov.cn/", "keywords": ["OPC", "超级创业者", "AI"]},
    {"name": "杭州市政府", "url": "https://www.hangzhou.gov.cn/", "keywords": ["OPC", "一人公司", "AI"]},
    {"name": "武汉市政府", "url": "https://www.wuhan.gov.cn/", "keywords": ["OPC", "一人公司", "AI"]},
    {"name": "成都市政府", "url": "https://www.chengdu.gov.cn/", "keywords": ["OPC", "一人公司", "AI"]},
]

def crawl_source(source):
    """Crawl a single government site for new OPC policies"""
    import requests
    from bs4 import BeautifulSoup

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        resp = requests.get(source['url'], headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find links containing keywords
        results = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            if any(kw in text for kw in source['keywords']):
                href = link['href']
                if not href.startswith('http'):
                    href = source['url'].rstrip('/') + '/' + href.lstrip('/')
                results.append({
                    'source': source['name'],
                    'title': text,
                    'url': href,
                    'found_at': datetime.now().isoformat()
                })
        return results
    except Exception as e:
        print(f"[Crawler] Error crawling {source['name']}: {e}")
        return []

def run_crawler():
    """Run full crawl cycle"""
    print(f"[Crawler] Starting crawl at {datetime.now()}")
    all_results = []
    for source in CRAWL_SOURCES:
        results = crawl_source(source)
        all_results.extend(results)

    if all_results:
        # Log new findings
        changes = load_changes()
        for r in all_results:
            # Deduplicate by URL hash
            url_hash = hashlib.md5(r['url'].encode()).hexdigest()
            existing = [c for c in changes['changes'] if c.get('url_hash') == url_hash]
            if not existing:
                r['url_hash'] = url_hash
                r['status'] = 'new'
                changes['changes'].append(r)
                print(f"[Crawler] NEW: {r['title']}")
        save_changes(changes)

    print(f"[Crawler] Done. Found {len(all_results)} total links, new ones saved.")
    return all_results

# ============================================================
# 3. POLICY CHANGE TRACKER
# ============================================================

def check_policy_changes():
    """Check for changes in existing policies (status, deadlines, etc.)"""
    data = load_policies()
    changes = load_changes()
    now = datetime.now()

    for policy in data.get('policies', []):
        # Check for upcoming deadlines
        deadline = policy.get('application', {}).get('deadline', '')
        if deadline:
            try:
                dl_date = datetime.strptime(deadline, '%Y-%m-%d')
                days_left = (dl_date - now).days
                if 0 < days_left <= 7:
                    changes['changes'].append({
                        'type': 'deadline_warning',
                        'policy_id': policy['id'],
                        'policy_name': policy['name'],
                        'deadline': deadline,
                        'days_left': days_left,
                        'found_at': now.isoformat()
                    })
            except ValueError:
                pass

        # Check expired policies
        expire = policy.get('expire_date', '')
        if expire:
            try:
                exp_date = datetime.strptime(expire, '%Y-%m-%d')
                if exp_date < now and policy.get('status') == 'active':
                    policy['status'] = 'expired'
                    changes['changes'].append({
                        'type': 'status_change',
                        'policy_id': policy['id'],
                        'policy_name': policy['name'],
                        'old_status': 'active',
                        'new_status': 'expired',
                        'found_at': now.isoformat()
                    })
            except ValueError:
                pass

    save_policies(data)
    save_changes(changes)

# ============================================================
# 4. NOTIFICATION SYSTEM
# ============================================================

def send_email_notification(to_email, subject, body):
    """Send email notification"""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    if not all([smtp_host, smtp_user, smtp_pass]):
        print(f"[Notification] SMTP not configured, skipping email to {to_email}")
        return False

    try:
        msg = MIMEText(body, 'html', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[Notification] Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"[Notification] Failed: {e}")
        return False

def notify_subscribers():
    """Notify subscribers about upcoming deadlines and new policies"""
    subs = load_subscribers()
    changes = load_changes()

    # Get recent changes (last 24h)
    recent = [c for c in changes.get('changes', [])
              if c.get('found_at', '') > (datetime.now() - timedelta(hours=24)).isoformat()]

    if not recent:
        return

    for sub in subs.get('subscribers', []):
        # Build notification
        body = "<h2>OPC政策更新提醒</h2><ul>"
        for c in recent:
            if c.get('type') == 'deadline_warning':
                body += f"<li>⚠️ <b>{c['policy_name']}</b> 将在 {c['days_left']} 天后截止 ({c['deadline']})</li>"
            elif c.get('status') == 'new':
                body += f"<li>🆕 发现新政策线索: <b>{c.get('title','')}</b> ({c.get('source','')})</li>"
        body += "</ul>"

        send_email_notification(sub['email'], '【OPC政策导航】政策更新提醒', body)

# ============================================================
# 5. AI POLICY ADVISOR
# ============================================================

def ai_advisor(user_profile, question):
    """Use Claude to answer policy questions"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not configured", "answer": "AI顾问功能需要配置 Anthropic API Key，请在 .env 文件中设置 ANTHROPIC_API_KEY"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Load policies as context
        data = load_policies()
        policies_text = json.dumps(data['policies'], ensure_ascii=False, indent=0)

        system_prompt = f"""你是一个专业的OPC（一人公司）政策顾问。你掌握全国各城市的OPC政策信息。

用户情况：
{json.dumps(user_profile, ensure_ascii=False)}

政策数据库（JSON）：
{policies_text[:30000]}

回答规则：
1. 基于政策数据库中的真实数据回答
2. 明确标注政策名称、城市、金额
3. 如果不确定，说明需要进一步确认
4. 给出具体的申报建议和步骤
5. 用简洁的中文回答，不要太长"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": question}]
        )

        return {"answer": message.content[0].text}
    except Exception as e:
        return {"error": str(e), "answer": f"AI顾问暂时不可用: {str(e)}"}

# ============================================================
# 6. MATCHING ENGINE (server-side)
# ============================================================

def match_policies_server(profile):
    """Server-side policy matching with full scoring"""
    data = load_policies()
    results = []

    for policy in data.get('policies', []):
        score = 0
        max_score = 0
        reasons = []
        blockers = []
        req = policy.get('requirements', {})

        # Location match (40 points)
        max_score += 40
        reg_loc = req.get('registration_location', '')
        if not reg_loc or reg_loc == '不限':
            score += 40
            reasons.append('不限注册地')
        elif profile.get('city', '') and profile['city'] in reg_loc:
            if profile.get('district', '') and profile['district'] in reg_loc:
                score += 40
                reasons.append(f"注册在{profile['district']}区，完全匹配")
            else:
                score += 30
                reasons.append(f"注册在{profile['city']}，市级匹配")
        elif profile.get('province', '') and (profile['province'] in reg_loc or policy.get('level') == 'province'):
            score += 20
            reasons.append('省级政策适用')
        else:
            score += 0
            blockers.append(f"要求在{reg_loc}注册/经营")

        # Company age (15 points)
        age_limit = req.get('company_age_max_years')
        if age_limit:
            max_score += 15
            user_age = profile.get('companyAge', 0)
            if user_age and user_age <= age_limit:
                score += 15
                reasons.append(f"公司成立{user_age}年，符合{age_limit}年内要求")
            elif user_age and user_age > age_limit:
                blockers.append(f"要求成立{age_limit}年内")
            else:
                score += 8

        # Social insurance (15 points)
        if req.get('social_insurance_months'):
            max_score += 15
            if profile.get('employees', 0) >= 1:
                score += 12
                reasons.append(f"有{profile['employees']}人缴社保")

        # Founder identity (15 points)
        founder_req = req.get('founder_identity', [])
        if founder_req:
            max_score += 15
            user_founder = profile.get('founder', [])
            if any(f in str(founder_req) for f in user_founder if f != '以上都不是'):
                score += 15
                reasons.append('法人身份符合')
            elif '以上都不是' in user_founder:
                blockers.append('法人身份不符合要求')
            else:
                score += 5

        # Qualifications (15 points)
        qual_req = req.get('qualifications', [])
        if qual_req:
            max_score += 15
            user_quals = profile.get('qualifications', [])
            if any(q in str(qual_req) for q in user_quals):
                score += 15
            else:
                if any('模型备案' in q for q in qual_req) and '有模型备案' not in user_quals:
                    blockers.append('需要模型备案')
                if any('算法备案' in q for q in qual_req) and '有算法备案' not in user_quals:
                    blockers.append('需要算法备案')

        pct = round((score / max_score) * 100) if max_score > 0 else 50
        level = 'low' if (blockers and pct < 40) else ('high' if pct >= 70 else 'mid')

        results.append({
            'policy': policy,
            'score': pct,
            'level': level,
            'reasons': reasons,
            'blockers': blockers
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# ============================================================
# 7. DASHBOARD DATA
# ============================================================

def get_dashboard_data():
    """Generate dashboard statistics"""
    data = load_policies()
    policies = data.get('policies', [])

    # City stats
    city_stats = {}
    for p in policies:
        city = p.get('city', 'unknown')
        if city not in city_stats:
            city_stats[city] = {'count': 0, 'max_amount': 0, 'categories': set(), 'communities': 0}
        city_stats[city]['count'] += 1
        for b in p.get('benefits', []):
            city_stats[city]['max_amount'] = max(city_stats[city]['max_amount'], b.get('amount_max', 0))
        city_stats[city]['categories'].add(p.get('category', ''))
        city_stats[city]['communities'] += len(p.get('communities', []))

    # Convert sets to lists for JSON
    for city in city_stats:
        city_stats[city]['categories'] = list(city_stats[city]['categories'])

    # Category distribution
    categories = {}
    for p in policies:
        cat = p.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1

    # Benefit type distribution
    benefit_types = {}
    total_max = 0
    for p in policies:
        for b in p.get('benefits', []):
            bt = b.get('type', 'other')
            benefit_types[bt] = benefit_types.get(bt, 0) + 1
            total_max += b.get('amount_max', 0)

    # Upcoming deadlines
    upcoming = []
    now = datetime.now()
    for p in policies:
        dl = p.get('application', {}).get('deadline', '')
        if dl:
            try:
                dl_date = datetime.strptime(dl, '%Y-%m-%d')
                days = (dl_date - now).days
                if 0 < days <= 60:
                    upcoming.append({'name': p['name'], 'city': p['city'], 'deadline': dl, 'days_left': days})
            except ValueError:
                pass
    upcoming.sort(key=lambda x: x['days_left'])

    # Verified vs unverified
    verified = sum(1 for p in policies if p.get('verified'))
    unverified = len(policies) - verified

    return {
        'total_policies': len(policies),
        'total_cities': len(city_stats),
        'total_communities': sum(cs['communities'] for cs in city_stats.values()),
        'total_max_amount': total_max,
        'city_stats': city_stats,
        'categories': categories,
        'benefit_types': benefit_types,
        'upcoming_deadlines': upcoming,
        'verified': verified,
        'unverified': unverified,
        'last_updated': data.get('updated_at', '')
    }

# ============================================================
# API ROUTES
# ============================================================

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/policies')
def api_policies():
    """Get all policies, optionally filtered"""
    data = load_policies()
    city = request.args.get('city')
    status = request.args.get('status')
    category = request.args.get('category')

    policies = data.get('policies', [])
    if city:
        policies = [p for p in policies if p.get('city') == city]
    if status:
        policies = [p for p in policies if p.get('status') == status]
    if category:
        policies = [p for p in policies if p.get('category') == category]

    return jsonify({'policies': policies, 'total': len(policies)})

@app.route('/api/match', methods=['POST'])
def api_match():
    """Match policies based on user profile"""
    profile = request.json
    results = match_policies_server(profile)

    high = len([r for r in results if r['level'] == 'high'])
    mid = len([r for r in results if r['level'] == 'mid'])
    low = len([r for r in results if r['level'] == 'low'])

    return jsonify({
        'results': results,
        'summary': {'high': high, 'mid': mid, 'low': low, 'total': len(results)}
    })

@app.route('/api/advisor', methods=['POST'])
def api_advisor():
    """AI policy advisor"""
    data = request.json
    profile = data.get('profile', {})
    question = data.get('question', '')

    if not question:
        return jsonify({'error': 'question is required'}), 400

    result = ai_advisor(profile, question)
    return jsonify(result)

@app.route('/api/dashboard')
def api_dashboard():
    """Dashboard data"""
    return jsonify(get_dashboard_data())

@app.route('/api/changes')
def api_changes():
    """Get policy changes/updates"""
    changes = load_changes()
    limit = int(request.args.get('limit', 50))
    return jsonify({
        'changes': changes.get('changes', [])[-limit:],
        'total': len(changes.get('changes', []))
    })

@app.route('/api/subscribe', methods=['POST'])
def api_subscribe():
    """Subscribe to policy update notifications"""
    data = request.json
    email = data.get('email', '')
    city = data.get('city', '')

    if not email:
        return jsonify({'error': 'email is required'}), 400

    subs = load_subscribers()
    # Check duplicate
    if any(s['email'] == email for s in subs.get('subscribers', [])):
        return jsonify({'message': '已订阅'})

    subs['subscribers'].append({
        'email': email,
        'city': city,
        'subscribed_at': datetime.now().isoformat()
    })
    save_subscribers(subs)
    return jsonify({'message': '订阅成功'})

@app.route('/api/calendar')
def api_calendar():
    """Get policy deadlines as calendar events"""
    data = load_policies()
    events = []

    for p in data.get('policies', []):
        dl = p.get('application', {}).get('deadline', '')
        if dl:
            events.append({
                'title': p['name'],
                'date': dl,
                'city': p.get('city', ''),
                'type': 'deadline',
                'url': p.get('links', {}).get('official', '')
            })

        nw = p.get('application', {}).get('next_window', '')
        if nw:
            events.append({
                'title': f"{p['name']} 申报窗口",
                'date': nw.split(' ')[0] if ' ' in nw else nw,
                'city': p.get('city', ''),
                'type': 'window'
            })

    events.sort(key=lambda x: x.get('date', ''))
    return jsonify({'events': events})

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    """Trigger manual crawl"""
    results = run_crawler()
    return jsonify({'message': f'Crawled {len(results)} links', 'results': results})

# ============================================================
# SCHEDULER
# ============================================================

scheduler = BackgroundScheduler()

def setup_scheduler():
    interval = int(os.getenv('CRAWL_INTERVAL_HOURS', 6))
    # Auto crawl
    scheduler.add_job(run_crawler, 'interval', hours=interval, id='auto_crawl')
    # Check changes daily
    scheduler.add_job(check_policy_changes, 'interval', hours=24, id='check_changes')
    # Notify subscribers daily
    scheduler.add_job(notify_subscribers, 'interval', hours=24, id='notify')
    scheduler.start()
    print(f"[Scheduler] Started. Crawl every {interval}h, check changes daily.")

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    setup_scheduler()
    port = int(os.getenv('PORT', 5000))
    print(f"[OPC Backend] Starting on port {port}")
    print(f"[OPC Backend] API docs: http://localhost:{port}/api/policies")
    app.run(host='0.0.0.0', port=port, debug=True)
