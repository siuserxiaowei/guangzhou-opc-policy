# OPC 后端服务

## 快速开始

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API key
python app.py
```

服务启动在 `http://localhost:5000`

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/policies` | GET | 获取所有政策，支持 `?city=广州&status=active&category=subsidy` |
| `/api/match` | POST | 智能匹配，传入用户画像 JSON |
| `/api/advisor` | POST | AI 政策顾问，传入 `{profile, question}` |
| `/api/dashboard` | GET | 数据看板统计 |
| `/api/calendar` | GET | 申报日历事件 |
| `/api/changes` | GET | 政策变动记录 |
| `/api/subscribe` | POST | 订阅通知，传入 `{email, city}` |
| `/api/crawl` | POST | 触发手动爬取 |

## 爬虫

```bash
# 完整爬取（所有城市）
python crawler.py

# 只爬取指定城市
python crawler.py --source 广州

# 提取单个URL的政策信息
python crawler.py --extract https://xxx.gov.cn/xxx
```

## 定时任务

后端内置 APScheduler：
- 每 6 小时自动爬取（可通过 `CRAWL_INTERVAL_HOURS` 配置）
- 每 24 小时检查政策变动（过期/截止提醒）
- 每 24 小时发送订阅通知邮件
