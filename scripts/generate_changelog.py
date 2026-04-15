#!/usr/bin/env python3
"""
生成 changelog.html：从 git log 自动提取维护日志，标注数据核验动作。
每次 commit 后手动或 GitHub Action 跑一次：
    python3 scripts/generate_changelog.py
"""
import subprocess
import re
import html
from pathlib import Path
from datetime import datetime
from collections import defaultdict

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / 'changelog.html'

GIT_FMT = '%H|%an|%ai|%s|%b---END---'

# commit subject 分类 -> (图标, 颜色, 标签)
CATEGORIES = [
    (r'^(苏州|广州|深圳|北京|成都|上海|杭州|重庆|天津|南京|武汉|西安|青岛|宁波|厦门|合肥|长沙|福州|郑州|济南|大连|无锡|苏州|昆山|吴江|太仓|常熟|东莞|佛山|珠海|中山|惠州|湛江|江门|肇庆|汕头|潮州|梅州|韶关|清远|阳江|茂名|河源|汕尾|揭阳|云浮)', '🏙️', 'city', '城市数据'),
    (r'^(文案|文档|docs?)', '📝', 'docs', '文档与文案'),
    (r'^(素材|迁移)', '📦', 'move', '素材迁移'),
    (r'^fix', '🔧', 'fix', '修复'),
    (r'^feat', '✨', 'feat', '新功能'),
    (r'^(ops|chore|CI|deploy)', '⚙️', 'ops', '运维'),
    (r'^(核实|核验|verify|debunk)', '🛡️', 'verify', '数据核实'),
    (r'^(add|新增)', '➕', 'add', '新增'),
]

def classify(subject):
    for pattern, icon, cls, label in CATEGORIES:
        if re.match(pattern, subject, re.IGNORECASE):
            return icon, cls, label
    return '📌', 'other', '其他'


def git_log():
    """抓取所有 commit，按时间倒序"""
    result = subprocess.run(
        ['git', 'log', f'--pretty=format:{GIT_FMT}', '--no-merges'],
        cwd=REPO, capture_output=True, text=True
    )
    commits = []
    for block in result.stdout.split('---END---'):
        block = block.strip()
        if not block:
            continue
        parts = block.split('|', 4)
        if len(parts) < 4:
            continue
        sha, author, iso_date, subject = parts[0], parts[1], parts[2], parts[3]
        body = parts[4] if len(parts) > 4 else ''
        try:
            dt = datetime.fromisoformat(iso_date.replace(' ', 'T', 1).replace(' ', ''))
        except Exception:
            try:
                dt = datetime.strptime(iso_date[:19], '%Y-%m-%d %H:%M:%S')
            except Exception:
                continue
        commits.append({
            'sha': sha[:7],
            'full_sha': sha,
            'author': author,
            'dt': dt,
            'subject': subject.strip(),
            'body': body.strip(),
        })
    return commits


def commit_stats(sha):
    """每个 commit 的文件变化统计"""
    result = subprocess.run(
        ['git', 'show', '--stat', '--format=', sha],
        cwd=REPO, capture_output=True, text=True
    )
    lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
    if not lines:
        return None
    last = lines[-1]
    m = re.search(r'(\d+)\s+file', last)
    files = int(m.group(1)) if m else 0
    m2 = re.search(r'(\d+)\s+insert', last)
    inserts = int(m2.group(1)) if m2 else 0
    m3 = re.search(r'(\d+)\s+delet', last)
    deletes = int(m3.group(1)) if m3 else 0
    return {'files': files, '+': inserts, '-': deletes}


def render_html(commits):
    total = len(commits)
    verified_count = sum(1 for c in commits if classify(c['subject'])[1] in ('verify', 'city'))
    month_stats = defaultdict(int)
    for c in commits:
        month_stats[c['dt'].strftime('%Y-%m')] += 1

    months_html = ''.join(
        f'<span class="m-chip">{month} · {n} 次</span>'
        for month, n in sorted(month_stats.items(), reverse=True)
    )

    items = []
    for c in commits:
        icon, cls, label = classify(c['subject'])
        date = c['dt'].strftime('%Y-%m-%d')
        time = c['dt'].strftime('%H:%M')
        subject = html.escape(c['subject'])
        body_text = c['body']
        if 'Co-Authored-By' in body_text:
            body_text = body_text.split('Co-Authored-By')[0].strip()
        body_html = ''
        if body_text:
            lines = [html.escape(l) for l in body_text.split('\n') if l.strip()]
            body_html = '<div class="cm-body">' + '<br>'.join(lines) + '</div>'
        stats = commit_stats(c['full_sha'])
        stats_html = ''
        if stats:
            stats_html = (
                f'<span class="cm-stats">'
                f'{stats["files"]} 文件 '
                f'<span class="st-plus">+{stats["+"]}</span> '
                f'<span class="st-minus">−{stats["-"]}</span>'
                f'</span>'
            )
        sha_link = (
            f'<a href="https://github.com/siuserxiaowei/opc-policy/commit/{c["full_sha"]}" '
            f'target="_blank" rel="noopener" class="cm-sha">{c["sha"]}</a>'
        )
        items.append(f'''
    <div class="cm-item cat-{cls}">
      <div class="cm-head">
        <span class="cm-icon">{icon}</span>
        <span class="cm-label">{label}</span>
        <span class="cm-date">{date} {time}</span>
        {sha_link}
        {stats_html}
      </div>
      <div class="cm-subject">{subject}</div>
      {body_html}
    </div>''')

    items_html = ''.join(items)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>维护日志 · 核实记录 | opcgate.com</title>
<meta name="description" content="opcgate.com 全部数据核验和更新日志。每条数据都可追溯到具体的 git commit，拒绝 AI 编造，每次改动都公开透明。">
<meta name="keywords" content="OPC政策 更新日志,核实日志,changelog,opcgate,数据核验">
<meta property="og:title" content="维护日志 · 核实记录 | opcgate.com">
<meta property="og:description" content="每条数据都可追溯到具体 commit，拒绝 AI 编造，每次改动都公开透明">
<meta property="og:type" content="article">
<meta property="og:url" content="https://opcgate.com/changelog.html">
<link rel="canonical" href="https://opcgate.com/changelog.html">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📋</text></svg>">
<style>
:root{{--bg:#0a0a0f;--card:#12121a;--card2:#1a1a28;--border:#2a2a3a;--text:#e0e0e8;--dim:#8888a0;
  --accent:#6c5ce7;--al:#a29bfe;--green:#00e676;--gd:#1b5e20;--yellow:#ffd600;--yd:#5d4e00;
  --red:#ff5252;--rd:#4a1515;--cyan:#00e5ff;--blue:#448aff;--orange:#ff9100}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);line-height:1.7}}
a{{color:var(--al);text-decoration:none}}a:hover{{color:#fff}}

.topnav{{display:flex;align-items:center;gap:8px;padding:10px 20px;background:rgba(10,10,15,.9);
  border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;backdrop-filter:blur(12px);overflow-x:auto}}
.topnav .logo{{font-weight:800;font-size:1em;color:var(--al)}}
.topnav a{{padding:6px 14px;border-radius:6px;font-size:.82em;color:var(--dim);transition:all .2s;white-space:nowrap}}
.topnav a:hover,.topnav a.active{{color:var(--al);background:rgba(108,92,231,.1)}}

.trust-slogan{{display:flex;align-items:center;justify-content:center;gap:10px;
  padding:8px 16px;background:linear-gradient(90deg,rgba(0,229,255,.06),rgba(108,92,231,.06),rgba(0,229,255,.06));
  border-bottom:1px solid rgba(0,229,255,.15);font-size:.78em;color:var(--cyan);font-weight:500}}
.trust-slogan .dot{{color:var(--dim);margin:0 4px}}

.hero{{padding:50px 20px 20px;text-align:center;background:linear-gradient(135deg,#0a0a1a,#1a0a2e,#0a1a3a)}}
.hero h1{{font-size:2em;font-weight:800;background:linear-gradient(135deg,#fff,var(--cyan),var(--al));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}}
.hero p{{color:var(--dim);font-size:.92em;max-width:720px;margin:0 auto 16px}}

.stats{{display:flex;justify-content:center;gap:12px;margin-top:16px;flex-wrap:wrap}}
.stats .s{{padding:10px 18px;background:var(--card);border:1px solid var(--border);border-radius:10px;min-width:130px}}
.stats .s .n{{font-size:1.6em;font-weight:800;color:var(--cyan)}}
.stats .s .l{{font-size:.72em;color:var(--dim);margin-top:2px}}

.container{{max-width:900px;margin:0 auto;padding:30px 20px}}

.months{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px;padding:14px 18px;background:var(--card);border:1px solid var(--border);border-radius:10px}}
.months .ml{{font-size:.82em;color:var(--dim);margin-right:4px}}
.m-chip{{padding:4px 10px;background:rgba(108,92,231,.08);border:1px solid rgba(108,92,231,.2);border-radius:14px;font-size:.76em;color:var(--al)}}

.cm-item{{background:var(--card);border:1px solid var(--border);border-left:3px solid var(--border);
  border-radius:10px;padding:16px 20px;margin-bottom:12px;transition:all .2s}}
.cm-item:hover{{border-color:rgba(108,92,231,.3);transform:translateX(2px)}}
.cm-item.cat-city{{border-left-color:var(--cyan)}}
.cm-item.cat-verify{{border-left-color:var(--green)}}
.cm-item.cat-feat{{border-left-color:var(--orange)}}
.cm-item.cat-fix{{border-left-color:var(--red)}}
.cm-item.cat-docs{{border-left-color:var(--al)}}
.cm-item.cat-move{{border-left-color:var(--blue)}}
.cm-item.cat-ops{{border-left-color:var(--yellow)}}

.cm-head{{display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap}}
.cm-icon{{font-size:1em}}
.cm-label{{font-size:.7em;font-weight:700;padding:2px 8px;background:rgba(255,255,255,.04);
  border:1px solid var(--border);border-radius:4px;color:var(--al);letter-spacing:.4px}}
.cm-date{{font-size:.78em;color:var(--dim);font-family:'JetBrains Mono',monospace}}
.cm-sha{{font-size:.72em;color:var(--cyan);font-family:'JetBrains Mono',monospace;
  background:rgba(0,229,255,.05);padding:1px 6px;border-radius:3px;border:1px solid rgba(0,229,255,.12)}}
.cm-sha:hover{{background:rgba(0,229,255,.12)}}
.cm-stats{{font-size:.72em;color:var(--dim);margin-left:auto}}
.st-plus{{color:var(--green);font-weight:600}}
.st-minus{{color:var(--red);font-weight:600}}

.cm-subject{{font-size:.95em;font-weight:600;color:var(--text);margin-bottom:6px}}
.cm-body{{font-size:.82em;color:var(--dim);line-height:1.7;padding:10px 12px;background:rgba(0,0,0,.2);border-radius:6px;margin-top:8px;border-left:2px solid rgba(108,92,231,.2);white-space:pre-wrap}}

footer{{text-align:center;padding:30px 20px;color:var(--dim);font-size:.78em;border-top:1px solid var(--border)}}
@media(max-width:640px){{.hero h1{{font-size:1.5em}}.stats .s{{min-width:calc(50% - 6px)}}.cm-head{{font-size:.88em}}.cm-stats{{margin-left:0}}}}
</style>
</head>
<body>

<nav class="topnav">
  <span class="logo">OPC</span>
  <a href="index.html">首页</a>
  <a href="guangzhou.html">广州专版</a>
  <a href="chengdu.html">成都专版</a>
  <a href="suzhou.html">苏州专版</a>
  <a href="yuexiu.html">越秀区</a>
  <a href="tax.html">税务指南</a>
  <a href="dashboard.html">数据看板</a>
  <a href="changelog.html" class="active">维护日志</a>
  <span style="flex:1"></span>
  <a href="https://github.com/siuserxiaowei/opc-policy" target="_blank" style="font-size:.78em">GitHub</a>
</nav>

<div class="trust-slogan">
  <span>🛡️</span>
  <span><strong>每条政策附官方链接</strong></span>
  <span class="dot">·</span>
  <span>拒绝 AI 编造</span>
  <span class="dot">·</span>
  <span>多源交叉核实</span>
  <span class="dot">·</span>
  <a href="index.html" style="color:var(--al)">返回首页</a>
</div>

<div class="hero">
  <h1>维护日志 · 核实记录</h1>
  <p>本页记录 opcgate.com 的所有数据核验、更新、修复动作。每条都可追溯到具体的 git commit，拒绝 AI 编造，每次改动都公开透明。</p>
  <div class="stats">
    <div class="s"><div class="n">{total}</div><div class="l">总维护次数</div></div>
    <div class="s"><div class="n">{verified_count}</div><div class="l">数据核验动作</div></div>
    <div class="s"><div class="n">{len(month_stats)}</div><div class="l">活跃月份</div></div>
    <div class="s"><div class="n" style="color:var(--green)">LIVE</div><div class="l">持续维护中</div></div>
  </div>
</div>

<div class="container">

  <div class="months">
    <span class="ml">按月分布：</span>
    {months_html}
  </div>

  {items_html}

</div>

<footer>
  <p>opcgate.com · 维护日志自动生成于 {now}</p>
  <p style="margin-top:4px"><a href="https://github.com/siuserxiaowei/opc-policy">在 GitHub 上查看完整提交历史 ↗</a></p>
</footer>

<!-- 百度自动推送 -->
<script>
(function(){{
  var bp = document.createElement('script');
  var curProtocol = window.location.protocol.split(':')[0];
  if (curProtocol === 'https') {{
    bp.src = 'https://zz.bdstatic.com/linksubmit/push.js';
  }} else {{
    bp.src = 'http://push.zhanzhang.baidu.com/push.js';
  }}
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(bp, s);
}})();
</script>
</body>
</html>
'''


def main():
    commits = git_log()
    print(f'Found {len(commits)} commits')
    html_content = render_html(commits)
    OUT.write_text(html_content)
    print(f'Wrote {OUT} ({len(html_content)} bytes)')


if __name__ == '__main__':
    main()
