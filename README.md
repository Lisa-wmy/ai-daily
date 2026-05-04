# AI-Daily · Daily AI Industry News

A Claude Code skill that fetches real AI industry news from the last 30 days and generates a beautiful HTML card interface.

---

## Features

- **Real-time News**: Fetches AI news from the past 30 days (sources: TechCrunch, The Verge, Wired, Ars Technica, and more)
- **Smart Tagging**: Each article auto-tagged with 1-3 professional labels
- **Filter Navigation**: Top tag buttons — click to filter by category
- **Company Tracking**: Auto-identifies companies mentioned (OpenAI, Google, Nvidia, etc.)
- **Important News Highlight**: Major events (funding/regulation/model releases) are marked in red
- **Bilingual Ready**: English pages with one-click translation via Edge browser

---

## Installation

### Option 1: Git Clone (Recommended)

```bash
git clone https://github.com/Lisa-wmy/ai-daily.git ~/.claude/skills/ai-daily
```

### Option 2: Manual Download

Download the repo, rename the folder to `ai-daily`, and place it in your Claude Code skills directory:
```
~/.claude/skills/ai-daily/
```

---

## Configure NewsAPI Key

1. Visit https://newsapi.org and register a free account
2. Copy your API Key
3. On first use, Claude Code will prompt you to enter the Key

---

## Usage

Simply say in Claude Code:

```
AI日报
AI资讯
今日AI动态
AI行业动态
```

Or in English:

```
Generate my AI daily
Show me today's AI news
```

Claude Code will guide you through three steps:

1. **Enter NewsAPI Key** (first-time only)
2. **Run fetch script**: Download 30 days of AI news → `news_raw.json`
3. **Run generate script**: Output a beautiful HTML daily report

Output file: `AI日报-YYYYMMDD.html` (or `AI-Daily-YYYYMMDD.html`). Open in any browser.

---

## News Tag System

| Tag | Coverage |
|-----|----------|
| AI模型与技术 | Model releases, benchmarks, research breakthroughs |
| AI基础设施 | Data centers, GPUs, chips, cloud services |
| AI融资与估值 | Funding rounds, IPOs, company valuations |
| AI政策与监管 | AI regulations, antitrust, government policies |
| AI商业应用 | Robots, autonomous driving, healthcare, enterprise software |
| AI安全伦理 | Data leaks, privacy, deepfakes, ethical risks |

---

## File Structure

```
├── skill.md           # Skill definition (read by Claude Code)
├── scripts/
│   ├── fetch_news.py  # News fetcher (NewsAPI + RSS)
│   └── gen_daily.py   # HTML report generator
└── evals/
    └── evals.json     # Eval configuration
```

---

## Requirements

- Python 3.8+
- `requests` library
- (Optional) `feedparser` for RSS subscription support

```bash
pip install requests feedparser
```

---

## Translate to Chinese

The report is generated in English. Open `AI日报-YYYYMMDD.html` with **Edge browser**, click the translate icon in the address bar — the entire page translates with one click.

