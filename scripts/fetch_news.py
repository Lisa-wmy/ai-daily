#!/usr/bin/env python3
"""
AI-Daily 新闻抓取脚本 v9 (每次询问 Key 版)
- NewsAPI Key 由调用者每次传入，不再依赖环境变量
- NewsAPI (更多查询) + RSS订阅（零成本）
- 全部来源直接链接到原网页
"""

import os, json, requests, time, re, argparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# 可选依赖
try:
    import feedparser
    FEEDPARSER_OK = True
except ImportError:
    FEEDPARSER_OK = False

def get_api_key():
    """从命令行参数读取 Key，若未传入则提示用户手动设置环境变量并退出"""
    parser = argparse.ArgumentParser(description='AI-Daily News Fetcher')
    parser.add_argument('--key', '-k', dest='api_key', default=None,
                        help='NewsAPI key (or set NEWS_API_KEY env var)')
    args = parser.parse_args()
    if args.api_key:
        return args.api_key.strip()
    key = os.environ.get("NEWS_API_KEY", "")
    if key:
        return key
    return None

NEWS_API_KEY = get_api_key()

# ------------------------------------------------------------------
# AI 相关性过滤
# ------------------------------------------------------------------
AI_POSITIVE_KEYWORDS = [
    # 公司级关键词（最强信号）
    'openai', 'anthropic', 'google deepmind', 'google ai', 'meta ai', 'microsoft ai',
    'amazon ai', 'apple ai', 'nvidia ai', 'xai ', 'mistral', 'perplexity',
    'chatgpt', 'claude ai', 'gemini', 'gpt-', 'llama', 'grok', 'deepseek', 'stability ai',
    'hugging face', 'cohere', 'scale ai', 'character ai', 'midjourney',
    # 模型/技术级关键词
    'large language model', ' llm ', 'llm,', 'ai model', 'generative ai', 'foundation model',
    'frontier ai', 'multimodal ai', 'reasoning model', 'neural network', 'deep learning',
    'transformer model', 'ai benchmark', 'machine learning', 'neural network',
    # AI 应用/产品级关键词
    'smartphone ai', 'ai smartphone', 'wearable ai', 'ai glasses', 'meta ray-ban',
    'humanoid robot', 'robotaxi', 'autonomous vehicle', 'self-driving car', 'robotics ai',
    'ai agent', 'ai assistant', 'ai chatbot', 'ai copilot', 'ai copilot',
    'ai chip', 'ai gpu', 'neuromorphic', 'tpu', 'quantum computing',
    # 行业级关键词
    'ai startup', 'ai funding', 'ai investment', 'ai valuation', 'ai ipo', 'ai acquisition',
    'ai regulation', 'ai policy', 'ai law', 'eu ai act', 'ai safety', 'ai alignment',
    'ai infrastructure', 'data center ai', 'stargate', 'nvidia ', 'amd gpu',
    'ai risk', 'ai governance', 'ai ethics', 'ai bias', 'deepfake',
]

AI_EXCLUDE_KEYWORDS = [
    # 消费电子（排除纯硬件报道）
    'iphone ', 'ipad ', 'macbook ', 'airpods ', 'apple watch', 'apple pencil',
    'android phone', 'samsung galaxy', 'pixel phone', 'galaxy s', 'galaxy z', 'oneplus',
    # 加密货币
    'crypto ', 'cryptocurrency', 'bitcoin', 'ethereum', 'nft ', 'solana', 'binance',
    # 汽车（非自动驾驶）
    'electric vehicle', 'ev startup', 'gas car', 'gasoline car', 'hybrid car', 'pickup truck',
    # 游戏（排除游戏评测/发行）
    'video game', 'playstation', 'xbox', 'nintendo switch', 'steam ', 'steam deck',
    'gaming laptop', 'esports', 'gaming industry', 'game review', 'game release',
    'game of the year', 'game developer conference',
    # 金融（非AI政策）
    'federal reserve', 'interest rate', 'inflation', 'gdp ',
    'stock market', 'bond market', 'currency',
    'housing market', 'mortgage',
    # 地缘政治（非AI监管）
    'trade war', 'tariff', 'sanctions',
    # 娱乐/生活（非AI应用）
    'sports ', 'football', 'basketball', 'soccer', 'baseball', 'tennis',
    'celebrity', 'hollywood', 'movie', 'music ', 'netflix', 'streaming',
    'restaurant', 'recipe', 'travel', 'hotel', 'flight deal', 'tourism',
]

# 所有媒体来源统一严格过滤，不再按"可信来源"自动放行
AI_TRUSTED_SOURCES = {
    'venturebeat', 'venturebeat.com', 'techcrunch', 'techcrunch.com',
    'the verge', 'theverge.com', 'wired', 'wired.com',
    'ars technica', 'arstechnica.com', 'engadget', 'engadget.com',
    'mit technology review', 'technologyreview.com', 'technologyreview',
    'business insider', 'businessinsider.com',
    'forbes ai', 'forbes.com',
    'reuters', 'reuters.com', 'bloomberg', 'bloomberg.com',
    'cnbc', 'cnbc.com',
}

# ------------------------------------------------------------------
# RSS 订阅来源（零成本，完全免费）
# ------------------------------------------------------------------
RSS_FEEDS = [
    ('VentureBeat',      'https://venturebeat.com/feed/',                          'ai'),
    ('MIT Tech Review',  'https://www.technologyreview.com/feed/',                  'ai'),
    ('The Verge',        'https://www.theverge.com/rss/index.xml',                  'ai'),
    ('Wired',            'https://www.wired.com/feed/rss',                          'ai'),
    ('Ars Technica',      'https://feeds.arstechnica.com/arstechnica/index',          'ai'),
    ('AI News',          'https://www.artificialintelligence-news.com/feed/',        'ai'),
    ('ZDNet',            'https://www.zdnet.com/news/rss/',                         'ai'),
    ('The Register',     'https://www.theregister.com/Main/Left.rss',               'ai'),
    ('TechRepublic',     'https://www.techrepublic.com/feed/',                       'ai'),
    ('SiliconANGLE',     'https://siliconangle.com/feed/',                          'ai'),
]


# ------------------------------------------------------------------
# 来源黑名单（直接排除，不参与任何匹配）
# ------------------------------------------------------------------
BLOCKED_SOURCES = [
    # 技术/开发者站点（非新闻）
    'pypi.org', 'pypi.python.org', 'python.org',
    # 低质量/非专业来源
    'bringatrailer.com', 'slickdeals.net', 'alltoc.com', 'betalist.com',
    'upwork.com', 'freerepublic.com', 'livedoor.com',
    'sentient-os.ai', 'slashdot.org',
    'intomobile.com', 'hoover.org', 'plos.org', 'retractionwatch.com',
    'globenewswire',
    # 消费生活类（含来源名匹配）
    'makeuseof.com', 'softpedia.com', 'thegadgeteer.com',
    'geeky-gadgets.com', 'geekytyrant.com', 'upsocl.com',
    'gamingonlinux.com',
    'geeky gadgets', 'the gadgeteer',
    # 中国大陆娱乐/社会媒体
    'cctv.com', 'sina.com.cn', 'sohu.com', '163.com', 'qq.com',
    'ifeng.com', 'toutiao.com',
    # 边缘娱乐/八卦媒体
    'yahoo entertainment', 'fox news', 'new york post', 'dailymail.com',
    'hollywood reporter', 'theblaze', 'breitbart',
    'the times of india', 'ibtimes.com.au',
    'vanguard', 'the week magazine',
    'mediamanam.com', 'new atlas', 'al jazeera english',
    # 非新闻平台
    'amazon.com', 'microsoft.com', 'cisco.com',
    'rt.com', 'gizmodo.com', 'digital journal', 'kqed.org',
    'nlppeople.com', 'sammobile.com',
    # 科技博客/泛媒体（含来源名匹配）
    'geekytyrant', 'futurism', 'seclists.org', 'storagereview.com',
    'the intercept', 'researchbuzz.me',
    'tweakstown',
    # 非财经专业媒体
    '24/7 wall st', 'the indian express',
    'verdict.co.uk', 'infosecurity magazine',
    'kpbs.org', 'cmswire.com',
    # 加密/科技博客垂直媒体
    'crypto briefing', 'the next web', 'decrypt', 'wccftech',
    # 编辑质量不足的科技博客
    'c-sharpcorner.com', 'makeuseof', 'geeky gadgets',
]

# ------------------------------------------------------------------
# 金融分析师视角：优先来源（专业科技/财经媒体，AI关联度高于均值）
# 这些来源的文章即使AI关键词较轻也保留
# ------------------------------------------------------------------
PREFERRED_SOURCES = {
    # 一线科技媒体
    'techcrunch', 'techcrunch.com',
    'the verge', 'theverge.com',
    'wired', 'wired.com',
    'ars technica', 'arstechnica.com',
    'engadget', 'engadget.com',
    'mit technology review', 'technologyreview.com', 'technologyreview',
    # 财经/商业媒体
    'forbes', 'forbes.com',
    'business insider', 'businessinsider.com',
    'cnbc', 'cnbc.com',
    'reuters', 'reuters.com',
    'bloomberg', 'bloomberg.com',
    'fortune', 'fortune.com',
    'the information', 'theinformation.com',
    'pymnts.com',
    # 二线但内容质量高
    'siliconangle', 'siliconangle.com',
    'zdnet', 'zdnet.com',
    'techradar', 'techradar.com',
    'cnet', 'cnet.com',
    'xda developers', 'xda-developers.com',
    'windows central', 'windowscentral.com',
    '9to5mac', '9to5mac.com',
    '9to5google', '9to5google.com',
    # 加密/区块链（AI+金融交叉）
    'decrypt', 'decrypt.co',
    'wccftech', 'wccftech.com',
    'cointelegraph',
    # 开源/研究社区
    'github.com',
    'medium', 'substack.com',
    # 中国财经媒体
    'caixinglobal', 'caixin.com',
    'scmp', 'south china morning post',
    # 英文综合媒体
    'bbc', 'bbc.com',
    'cnn', 'cnn.com',
    'the atlantic', 'theatlantic.com',
    'npr', 'npr.org',
    'the guardian', 'theguardian.com',
    # 行业研究/安全
    'infosecurity magazine', 'infosecurity-magazine.com',
    'threatpost', 'threatpost.com',
    'securityweek', 'securityweek.com',
    'verdict', 'verdict.com',
    'computing', 'computerweekly.com',
    'tech target', 'techtarget.com',
    # AI/ML垂直媒体
    'venturebeat', 'venturebeat.com',
    'deepmind', 'deepmind.google',
    'huggingface', 'huggingface.co',
    # 数据/产业媒体
    'digitimes.com', 'digitimes.com.tw',
    # 财经垂直媒体
    'financial post', 'financialpost.com',
    'livemint', 'livemint.com',
    'the next web', 'thenextweb.com',
    # AI/算力/芯片垂直
    'tomshardware', 'tomshardware.com',
    'anandtech', 'anandtech.com',
    'serve-the-home',
}

def _normalize_article(title, url, source, publishedAt, description) -> dict:
    # 将UTC时间转换为中国标准时间(CST, UTC+8)，取其日期
    if publishedAt and 'T' in publishedAt:
        try:
            ts_clean = publishedAt.replace('Z', '+00:00')
            dt_utc = datetime.fromisoformat(ts_clean)
            cst = dt_utc + timedelta(hours=8)
            date = cst.strftime('%Y-%m-%d')
            ts_out = dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            date = publishedAt[:10]
            ts_out = publishedAt
    else:
        date = datetime.now().strftime('%Y-%m-%d')
        ts_out = publishedAt or f"{date}T00:00:00Z"
    return {
        'title': title,
        'url': url,
        'source': source,
        'publishedAt': ts_out,
        'date': date,
        'description': description or '',
    }


def _source_blocked(source: str) -> bool:
    s = source.lower()
    return any(b in s for b in BLOCKED_SOURCES)


def _source_match(source: str) -> bool:
    s = source.lower()
    return any(t in s for t in AI_TRUSTED_SOURCES)


def _is_likely_ai_article(title: str, desc: str, source: str = '') -> bool:
    combined = (title + ' ' + desc).lower()
    sl = source.lower()

    # 优先来源：AI关键词命中1个即通过
    if any(p in sl for p in PREFERRED_SOURCES):
        excl_hit = sum(1 for w in AI_EXCLUDE_KEYWORDS if w in combined)
        if excl_hit >= 2:
            return False
        return any(w in combined for w in AI_POSITIVE_KEYWORDS)

    # 非优先来源：必须命中2个AI关键词，且排除词不超过1个
    ai_hits = sum(1 for w in AI_POSITIVE_KEYWORDS if w in combined)
    excl_hit = sum(1 for w in AI_EXCLUDE_KEYWORDS if w in combined)
    if excl_hit >= 2:
        return False
    return ai_hits >= 2


def _dedup_and_filter(articles: list) -> list:
    seen_urls = set()
    seen_titles_norm = {}  # platform -> {normalized_title -> article}
    kept = []
    for a in articles:
        url = a.get('url', '')
        title = a.get('title', '')
        source = a.get('source', '')
        desc = a.get('description', '')
        if not url or not title or title == '[Removed]' or url in seen_urls:
            continue
        if _source_blocked(source):
            continue
        seen_urls.add(url)
        if not _is_likely_ai_article(title, desc, source):
            continue
        # 平台内标题去重：归一化后若30天内重复则跳过（保留首次）
        plat_key = source.strip()
        norm_title = re.sub(r'[\'".,;:!?\-–—]', '', title.lower())
        norm_title = re.sub(r'\s+', ' ', norm_title).strip()[:100]
        if plat_key not in seen_titles_norm:
            seen_titles_norm[plat_key] = {}
        if norm_title in seen_titles_norm[plat_key]:
            continue
        seen_titles_norm[plat_key][norm_title] = True
        kept.append(a)
    return kept


# ==================================================================
# 来源 1: NewsAPI（扩展更多域名）
# ==================================================================
def _fetch_newsapi(queries, headers, date_from, date_to) -> list:
    if not NEWS_API_KEY:
        print("[INFO] NEWS_API_KEY not set — skipping NewsAPI")
        return []

    domains = (
        "techcrunch.com,theverge.com,wired.com,venturebeat.com,"
        "reuters.com,bloomberg.com,cnbc.com,MIT.edu,arstechnica.com,"
        "engadget.com,theinformation.com,businessinsider.com,"
        "technologyreview.com,forbes.com,"
        "zdnet.com,axios.com,theregister.com,techmonitor.ai,"
        "datacenterfrontier.com,therecord.media,"
        "fortune.com,pymnts.com,siliconangle.com"
    )

    def fetch_batch(batch_qs):
        """将多个查询词合并为1次API调用，节省配额，同时限制域名范围"""
        combined_q = ' OR '.join(f'({q})' for q in batch_qs)
        params = {
            "q": combined_q,
            "domains": domains,
            "from": date_from,
            "to": date_to,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
        }
        for attempt in range(2):
            try:
                r = requests.get(
                    "https://newsapi.org/v2/everything",
                    headers=headers,
                    params=params,
                    timeout=15,
                )
                data = r.json()
                if data.get("status") == "ok":
                    results = []
                    for a in data.get("articles", []):
                        url = a.get("url", "")
                        title = a.get("title", "")
                        pub = a.get("publishedAt", "")
                        if url and title and title != "[Removed]":
                            results.append(_normalize_article(
                                title, url,
                                a.get("source", {}).get("name", "Unknown"),
                                pub,
                                a.get("description", "") or "",
                            ))
                    return results
                elif data.get("status") == "error":
                    # 配额耗尽时静默返回空列表，不中断整体抓取
                    print(f"  [NewsAPI] {data.get('message', 'error')}")
                    return []
            except Exception:
                if attempt < 1:
                    time.sleep(2)
        return []

    # 批量：将3个查询合并为1次API调用，节省配额
    BATCH_SIZE = 3
    batches = [queries[i:i+BATCH_SIZE] for i in range(0, len(queries), BATCH_SIZE)]
    articles = []
    with ThreadPoolExecutor(max_workers=min(len(batches), 6)) as ex:
        futures = [ex.submit(fetch_batch, batch) for batch in batches]
        for f in as_completed(futures):
            articles.extend(f.result())
    return articles


# ==================================================================
# 来源 2: RSS 订阅（零成本，无限抓取）
# ==================================================================
def _fetch_rss_source(name: str, feed_url: str) -> list:
    if not FEEDPARSER_OK:
        print(f"  [RSS] {name}: feedparser not installed, skipping")
        return []

    try:
        feed = feedparser.parse(feed_url)
        articles = []
        cutoff = datetime.now() - timedelta(days=30)

        for entry in feed.entries:
            title = getattr(entry, 'title', '') or ''
            url = getattr(entry, 'link', '') or getattr(entry, 'id', '') or ''
            if not title or not url:
                continue

            pub_raw = ''
            pub_date = getattr(entry, 'published', '') or getattr(entry, 'updated', '') or ''
            if pub_date:
                try:
                    from email.utils import parsedate_to_datetime
                    dt = parsedate_to_datetime(pub_date)
                    pub_raw = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    if dt < cutoff:
                        continue
                except Exception:
                    pub_raw = ''

            desc = ''
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '') or ''
            if summary:
                desc = re.sub(r'<[^>]+>', '', summary).strip()[:200]

            articles.append(_normalize_article(title.strip(), url.strip(), name, pub_raw, desc))

        print(f"  [RSS] {name}: {len(articles)} articles (from {feed_url})")
        return articles

    except Exception as e:
        print(f"  [RSS] {name} failed: {e}")
        return []


def _fetch_all_rss() -> list:
    print("[INFO] Fetching RSS feeds (zero cost)...")
    articles = []
    with ThreadPoolExecutor(max_workers=len(RSS_FEEDS)) as ex:
        futures = {ex.submit(_fetch_rss_source, name, url): name for name, url, _ in RSS_FEEDS}
        for f in as_completed(futures):
            articles.extend(f.result())
    return articles


# ==================================================================
# 主入口
# ==================================================================
def fetch_ai_news() -> list:
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    date_to = datetime.now().strftime("%Y-%m-%d")

    all_articles = []

    # 来源 1: NewsAPI（扩展到 15 个查询，覆盖更广）
    if NEWS_API_KEY:
        print("[INFO] Fetching from NewsAPI...")
        headers = {"X-Api-Key": NEWS_API_KEY}
        queries = [
            '"OpenAI" OR "ChatGPT" OR "GPT-5"',
            '"Anthropic" OR "Claude" OR "Claude AI"',
            '"Google AI" OR "Gemini" OR "DeepMind"',
            '"Meta AI" OR "LLaMA" OR "Llama 4"',
            '"xAI" OR "Grok" OR "Mistral AI"',
            '"AI model" OR "large language model" OR "LLM"',
            '"generative AI" OR "AI startup" OR "AI company"',
            '"AI assistant" OR "AI chatbot" OR "AI agent"',
            '"AI regulation" OR "AI policy" OR "AI law" OR "EU AI Act"',
            '"AI funding" OR "AI investment" OR "AI valuation"',
            '"AI application" OR "AI deployment" OR "AI adoption"',
            '"AI safety" OR "AI alignment" OR "frontier AI"',
            '"humanoid robot" OR "autonomous AI" OR "AI robotics"',
            '"AI chip" OR "AI GPU" OR "Nvidia" OR "AI infrastructure"',
            '"multimodal AI" OR "reasoning model" OR "AI benchmark"',
            '"AI agent" OR "AI copilot" OR "AI enterprise"',
            '"AI data center" OR "AI power" OR "AI energy"',
            '"AI healthcare" OR "AI medical" OR "AI drug discovery"',
            '"AI competition" OR "AI race" OR "OpenAI valuation"',
            '"AI semiconductor" OR "AI chip shortage" OR "AMD AI"',
            '"AI workforce" OR "AI hiring" OR "AI labor"',
            '"AI energy consumption" OR "AI carbon" OR "AI sustainability"',
        ]
        all_articles.extend(_fetch_newsapi(queries, headers, date_from, date_to))

    # 来源 2: RSS（零成本）
    rss_articles = _fetch_all_rss()
    all_articles.extend(rss_articles)

    # 去重 + 相关性过滤
    all_articles = _dedup_and_filter(all_articles)
    all_articles.sort(key=lambda x: x["publishedAt"], reverse=True)

    from collections import Counter
    srcs = Counter(a.get('source', 'Unknown') for a in all_articles)
    print(f"\n[SUMMARY] Total: {len(all_articles)} articles")
    for name, cnt in srcs.most_common():
        print(f"  {name}: {cnt}")

    return all_articles


if __name__ == "__main__":
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8")
    print("[INFO] AI-Daily v9 — Multi-source fetcher (key prompt mode)")
    print(f"       feedparser: {'OK' if FEEDPARSER_OK else 'MISSING (pip install feedparser)'}")
    if not NEWS_API_KEY:
        print("[ERROR] NewsAPI key not provided.")
        print("        Please provide via --key argument or set NEWS_API_KEY env var.")
        print("        Usage: python fetch_news.py --key YOUR_API_KEY")
        _sys.exit(1)
    print("[INFO] Fetching AI news (last 30 days) from NewsAPI + RSS...")
    articles = fetch_ai_news()
    if articles:
        out_path = "news_raw.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved {len(articles)} articles to {out_path}")
        dates = {}
        for a in articles:
            d = a['date']
            dates[d] = dates.get(d, 0) + 1
        print(f"[INFO] Date distribution: {dates}")
    else:
        print("[WARN] No articles fetched. Check NEWS_API_KEY or network connection.")
