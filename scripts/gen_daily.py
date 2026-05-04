#!/usr/bin/env python3

"""

AI-Daily 日报生成脚本 v5

- 每条新闻打1-3个标签（可叠加）

- 公司追踪（搜索框 + 快捷按钮）

- 重要新闻标红

- 全部新闻按时间倒序

- 顶部标签导航 + 公司搜索，点击筛选（原生JS）

"""

import json, sys, os, re

from datetime import datetime, timedelta



sys.stdout.reconfigure(encoding='utf-8')



TAGS = {

    'AI模型与技术':    '#96CEB4',

    'AI基础设施':      '#45B7D1',

    'AI融资与估值':    '#FF6B6B',

    'AI政策与监管':    '#4ECDC4',

    'AI商业应用':      '#DDA0DD',

    'AI安全伦理':      '#FF9F43',

}



TAG_RULES = [

    ('AI模型与技术', ['gpt-','claude','gemini','llama','muse','mistral','model','benchmark',

                     'research','breakthrough','frontier ai','distill','superintelligence',

                     'parameter','goblin','openai','anthropic','deepmind','humanoid ai',

                     'agent model','scaling law','neural','algorithm','mythos','cyberg']),

    ('AI基础设施',   ['data center','datacenter','gpu','chip','nvidia','amd','intel',

                     'semiconductor','cloud','aws','azure','stargate','infrastructure',

                     'energy','power','blackwell','h100','gb300','nscale','electr']),

    ('AI融资与估值', ['raise','funding','investor','valuation',' ipo ','series a','series b',

                     'seed round',' vc ','venture capital','backed by','softbank','a16z',

                     'thiel capital','angel allocat','pre-emptive']),

    ('AI政策与监管', ['regulation','policy','congress','senate',' pentagon','doj','government',

                     'federal','trump','white house','antitrust','unwind','veto','ban',

                     'restrict','liability','ai law','compliance','gdpr','uk gov','european',

                     'china veto','meta-manus','manus deal','china blocks']),

    ('AI商业应用',   ['autonomous','self-driving','robot','humanoid','healthcare','medical',

                     'legal','finance','enterprise','copilot','agent','smart','device',

                     'tesla',' gm ','vehicle','ar/vr','metaverse','wearable','glasses',

                     'smartphone','app','saas','business ai','customer','workplace']),

    ('AI安全伦理',   ['safety','security','cyber','hack','privacy','bias','ethics','deepfake',

                     'misinformation','vulnerability','risk','harm','whistleblow','attack',

                     'abuse','exploit','malware','nsfw','porn ai']),

]



HIGH_AUTHORITY_SOURCES = {

    'reuters', 'bloomberg', 'cnbc', 'wall street journal',

    'financial times', 'nyt', 'new york times', 'wsj',

}

MEDIA_AUTHORITY_SOURCES = {

    'techcrunch', 'the verge', 'wired', 'ars technica',

    'mit technology review', 'mit tech review', 'business insider',

    'forbes', 'the information', 'theatlantic', 'economist',

    'guardian', 'bbc', 'npr', 'ap news', 'associated press',

    'scientific american', 'fortune',

}

TIER1_COMPANIES = {'openai', 'anthropic', 'google', 'deepmind', 'meta', 'microsoft',

                    'nvidia', 'amazon', 'apple', 'tesla', 'xai', 'softbank'}

TIER2_COMPANIES = {'mistral', 'perplexity', 'cohere', 'hugging face', 'databricks',

                    'scale ai', 'stability ai', 'character.ai', 'midjourney',

                    'figure ai', 'samsung', 'a16z', 'sequoia', 'deepseek'}



# 事件类型权重（金融分析师视角）

EVENT_WEIGHTS = {

    # 一级：直接影响估值/行业格局（权重5）

    'direct_major': [

        'raise $', 'raised $', 'seed round', 'series a', 'series b', 'series c',

        'series d', 'ipo ', 'initial public', 'acquisition', 'acquire',

        'congress', 'senate hearing', 'federal investigation', 'doj', 'ftc',

        'antitrust', 'break up', 'ban ', 'veto', 'executive order',

        'security breach', 'data leak', 'massive hack',

    ],

    # 二级：重大商业/技术变化（权重4）

    'direct_medium': [

        '$500 million', '$1 billion', '$10 billion', 'valuation',

        'layoffs', 'shutdown', 'restructure', 'departure', 'resigns',

        'ceo ', 'founder', 'departure', 'replaced', 'fired',

        'flagship', 'frontier model', 'next generation',

        'chip ban', 'china blocks', 'china ban',

        'white house', 'pentagon', 'regulation',

    ],

    # 三级：重要产品/合作（权重3）

    'direct_minor': [

        'partnership', 'collaboration', 'exclusive deal',

        'launch', 'release', 'announce',

        'gpt-5', 'claude 4', 'gemini 2', 'llama 4',

        'o3', 'o4', 'deepseek r1', 'reasoning model',

        'zero-day', 'exploit', 'critical vulnerability',

        'lawsuit', 'litigation', 'settlement', 'fine',

        'jensen huang', 'sam altman', 'dario amend', 'mark zuckerberg',

    ],

    # 四级：二级市场关注（权重2）

    'indirect': [

        'gpt-', 'claude', 'gemini', 'llama', 'model',

        'agentic', 'ai agent', 'multimodal',

        'data center', 'infrastructure',

        'investor', 'funding', 'valuation',

    ],

}





def is_important(title, desc, source):

    tl = (title + ' ' + desc).lower()

    sl = source.lower()



    # 事件类型得分

    score = 0

    if any(k in tl for k in EVENT_WEIGHTS['direct_major']):

        score = 5

    elif any(k in tl for k in EVENT_WEIGHTS['direct_medium']):

        score = 4

    elif any(k in tl for k in EVENT_WEIGHTS['direct_minor']):

        score = 3

    elif any(k in tl for k in EVENT_WEIGHTS['indirect']):

        score = 1



    # 无重大事件不标记

    if score == 0:

        return False

    if score == 1:

        return False  # 仅含AI关键词的新闻不算重要



    # 公司层级乘数

    company_mult = 1

    if any(c in tl for c in TIER1_COMPANIES):

        company_mult = 2.0

    elif any(c in tl for c in TIER2_COMPANIES):

        company_mult = 1.5



    # 来源权威乘数（市场信息源 vs 普通媒体）

    if any(s in sl for s in HIGH_AUTHORITY_SOURCES):

        pass  # 不额外加分，保持权重

    elif any(s in sl for s in MEDIA_AUTHORITY_SOURCES):

        pass  # 同上



    final_score = score * company_mult



    # 阈值：综合得分 >= 8 才标红（约覆盖前11%，属于真正重要的）

    return final_score >= 8





def get_importance_score(title, desc, source):
    tl = (title + ' ' + desc).lower()
    score = 0
    if any(k in tl for k in EVENT_WEIGHTS['direct_major']):
        score = 5
    elif any(k in tl for k in EVENT_WEIGHTS['direct_medium']):
        score = 4
    elif any(k in tl for k in EVENT_WEIGHTS['direct_minor']):
        score = 3
    elif any(k in tl for k in EVENT_WEIGHTS['indirect']):
        score = 1
    else:
        return 0
    company_mult = 1.0
    if any(c in tl for c in TIER1_COMPANIES):
        company_mult = 2.0
    elif any(c in tl for c in TIER2_COMPANIES):
        company_mult = 1.5
    return score * company_mult


def _extract_funding_amount(text):
    tl = text.lower()
    amounts = []
    for pat, mult in [
        (r'\$?\s*([\d\.]+)\s*billion', 1e9),
        (r'\$?\s*([\d\.]+)\s*million', 1e6),
        (r'¥\s*([\d\.]+)\s*billion', 1e9),
    ]:
        for m in re.findall(pat, tl):
            try:
                amounts.append(float(m) * mult)
            except ValueError:
                pass
    return amounts


def _format_date_short(publishedAt):
    if publishedAt and 'T' in str(publishedAt):
        try:
            cst = datetime.fromisoformat(str(publishedAt).replace('Z', '+00:00')) + timedelta(hours=8)
            return cst.strftime('%m-%d')
        except Exception:
            pass
    return ''


def _clean_sentence(s):
    s = re.sub(r'<[^>]+>', '', s).strip()
    s = re.sub(r'\s*[-–—]\s*The post.*$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'^(the post|originally published at|read more at|copyright|via|image:|image credit:|disclosure:|sponsored|follow us on|subscribe to|sign up for|newsletter|appeared first on).*', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'https?://\S+', '', s).strip()
    return s


def generate_summary_line(a):
    title = a.get('title', '') or ''
    desc = a.get('description', '') or ''
    tl = (title + ' ' + desc).lower()

    # 融资事件
    if any(k in tl for k in ['raise', 'funding', 'raised', 'secured', 'investment of']):
        amounts = _extract_funding_amount(title + ' ' + desc)
        companies = a.get('_company', [])
        company = (companies[0] if isinstance(companies, list) and companies
                   else (companies or ''))
        if not company:
            for name in TIER1_COMPANIES | TIER2_COMPANIES:
                if name.lower() in tl:
                    company = name
                    break
        if amounts:
            amt = amounts[0]
            amt_str = f'${amt/1e9:.1f}B' if amt >= 1e9 else f'${amt/1e6:.0f}M'
            base = f'{company} 获得 {amt_str} 融资' if company else f'某AI公司获 {amt_str} 融资'
        else:
            base = f'{company} 完成新一轮融资' if company else 'AI公司完成新一轮融资'
        sent = _clean_sentence(_extract_sentence(desc, tl))
        return (base + '：' + sent) if sent else base + '。'

    # 模型发布
    model_kw = ['gpt-', 'claude', 'gemini', 'llama', 'mistral', 'deepseek', ' o3', ' o4', 'r1']
    for kw in model_kw:
        if kw in tl:
            for name, keywords in COMPANY_MAP.items():
                if any(k in tl for k in keywords):
                    sent = _clean_sentence(_extract_sentence(desc, tl))
                    if sent:
                        return f'{name} 发布新一代AI模型：{sent}'
                    if len(title) > 15:
                        return title.rstrip('.。') + '。'
                    return f'{name} 发布新一代AI模型。'
            sent = _clean_sentence(_extract_sentence(desc, tl))
            return ('头部AI公司发布新一代模型：' + sent) if sent else '头部AI公司发布新一代模型。'

    # 政策监管
    if any(k in tl for k in ['regulation', 'ban', 'antitrust', 'congress', 'eu ai act', 'policy', 'veto']):
        sent = _clean_sentence(_extract_sentence(desc, tl))
        if 'china' in tl or 'chinese' in tl:
            base = '中国AI监管/出口管制政策有新动向'
        elif 'eu ' in tl or 'europe' in tl:
            base = '欧盟AI监管政策有新进展'
        elif 'trump' in tl or 'executive order' in tl:
            base = '美国政府出台AI相关行政令'
        else:
            base = 'AI行业迎来重大监管政策变动'
        return (base + '：' + sent) if sent else base + '。'

    # 基础设施
    if any(k in tl for k in ['data center', 'stargate', 'infrastructure', 'gpu cluster']):
        sent = _clean_sentence(_extract_sentence(desc, tl))
        base = 'AI基础设施领域有大额投资或合作公告'
        return (base + '：' + sent) if sent else base + '。'
    if 'jensen huang' in tl or 'nvidia announce' in tl:
        sent = _clean_sentence(_extract_sentence(desc, tl))
        base = 'Nvidia 发布新一代AI芯片或平台'
        return (base + '：' + sent) if sent else base + '。'

    # 安全泄露
    if any(k in tl for k in ['breach', 'hack', 'leak', 'data leak', 'security']):
        sent = _clean_sentence(_extract_sentence(desc, tl))
        base = 'AI公司发生安全泄露或数据事件'
        return (base + '：' + sent) if sent else base + '。'

    # 高管变动
    if any(k in tl for k in ['resign', 'departure', 'fired', 'ceo', 'founder departure']):
        sent = _clean_sentence(_extract_sentence(desc, tl))
        base = 'AI公司高管发生重大人事变动'
        return (base + '：' + sent) if sent else base + '。'

    # 默认：取描述中一句不重复标题的完整句子
    sent = _clean_sentence(_extract_sentence(desc, tl))
    if sent:
        overlap = sum(1 for w in sent.lower().split() if w in tl and len(w) > 4)
        if overlap / max(len(sent.split()), 1) <= 0.6:
            return sent
    title_clean = re.sub(r'\s*[-–—]\s*The post.*$', '', title, flags=re.IGNORECASE).strip()
    return title_clean.rstrip('.。') + '。' if title_clean else (desc[:120].strip().rstrip('.。') + '。')


def _get_top_articles(articles, n=5):
    scored = [(get_importance_score(a['title'], a['description'], a['source']), a) for a in articles]
    scored = [(s, a) for s, a in scored if s > 0]
    scored.sort(key=lambda x: -x[0])
    return [a for _, a in scored[:n]]


def _normalize_for_compare(text):
    """提取文本核心词用于相似度比较（大写转小写、去除数字和通用词）"""
    text = text.lower()
    text = re.sub(r'[\$¥€£]\s*[\d.]+[bm]?', '', text)
    text = re.sub(r'\d+(?:\.\d+)?%', '', text)
    text = re.sub(r'\b\d{1,3}(?:,\d{3})+\b', '', text)
    # 用词边界替换，避免公司名作为子串被错误删除
    for name in COMPANY_MAP:
        for kw in COMPANY_MAP[name]:
            text = re.sub(r'\b' + re.escape(kw.lower()) + r'\b', ' ', text)
    STOP = {
        'artificial', 'intelligence', 'company', 'firm', 'inc', 'ltd', 'llc',
        'software', 'technology', 'tech', 'today', 'year', 'month', 'week',
        'million', 'billion', 'dollar', 'fund', 'raise', 'funding',
        'announce', 'announced', 'announces', 'disclose', 'disclosing',
        'deal', 'including', 'part', 'say', 'said', 'report', 'according',
    }
    for w in STOP:
        text = re.sub(r'\b' + re.escape(w) + r'\b', ' ', text)
    tokens = [w for w in re.split(r'[\W]+', text) if len(w) > 4]
    return set(tokens)


def _bow_sim(line1, line2):
    """词袋相似度：交集词数 / 较小集合的词数。>= 0.5 视为高相似"""
    s1 = _normalize_for_compare(line1)
    s2 = _normalize_for_compare(line2)
    if not s1 or not s2:
        return 0
    inter = len(s1 & s2)
    smaller = min(len(s1), len(s2))
    return inter / smaller if smaller > 0 else 0


def _clean_sentence(s):
    """规范化句子：去除首尾空白，去除RSS来源归属噪声"""
    if not s:
        return ''
    s = s.strip()
    sl = s.lower()
    if len(s) < 20:
        return ''
    # 跳过RSS来源归属噪声（前缀或含有关键词）
    noise_prefix = ('the post ', 'originally published at', 'read more at', 'copyright ',
                    'via ', 'image:', 'image credit:', 'disclosure:', 'sponsored',
                    'follow us on', 'subscribe to', 'sign up for', 'newsletter',
                    'you might also like', 'related articles',
                    'advertisement', 'sponsored content', 'partner content')
    noise_contains = ('appeared first on', '文章轉載', '轉載自', '來源：', '原文連結')
    if any(sl.startswith(p) for p in noise_prefix):
        return ''
    if any(p in sl for p in noise_contains):
        return ''
    if re.search(r'https?://|www\.', sl):
        return ''
    return s[:200]


def _extract_sentence(desc, tl, title_words=None):
    """从描述中提取一句完整句子，排除RSS来源归属噪声，过滤截断碎片"""
    if not desc:
        return ''
    # 检测描述是否被截断（以非完整句子结尾，如 "in to..." 或缺词）
    TRUNCATED_INDICATORS = ('...', '…', 'and mor', 'more det', 'for mor',
                             'this wa', 'they ha', 'it was', 'in mid-', 'the ne')
    desc_lc = desc.lower()
    is_truncated = (desc.endswith('...') or desc.endswith('…') or
                     any(desc_lc.endswith(x) for x in TRUNCATED_INDICATORS))
    if is_truncated:
        return ''
    NOISE_PREFIXES = (
        'the post ', 'originally published at', 'read more at', 'copyright ',
        'via ', 'image:', 'image credit:', 'disclosure:', 'sponsored',
        'follow us on', 'subscribe to', 'sign up for', 'newsletter',
        'appeared first on', 'you might also like', 'related articles',
        'advertisement', 'sponsored content', 'partner content',
        '文章轉載', '轉載自', '來源：', '原文連結', '未經授權',
    )
    sentences = re.split(r'[\n\r]+|[.!?。！？]', desc)
    for s in sentences:
        s = s.strip()
        sl = s.lower()
        # 句子太短（<20字符）或似乎被截断则跳过
        if len(s) < 20:
            continue
        # 跳过以逗号/非完整词开头的句子碎片（如 "C, school shooting..." 来自 "B.C." 分割）
        if re.match(r'^[,;\s]', s):
            continue
        # 跳过以非首字母大写词开头的碎片（真正的句子首词应大写）
        if re.match(r'^(and|but|or|so|because|which|who|that|when|where|how|while|with|from|to|in|on|at|for|a|an|the|its|their|his|her|this|these|those|itself|themselves)\s', sl):
            continue
        if any(sl.startswith(p) for p in NOISE_PREFIXES):
            continue
        # 过滤含归属噪声关键词的句子（如 "appeared first on" 混入中文描述）
        if any(p in sl for p in NOISE_PREFIXES):
            continue
        if re.search(r'https?://|www\.', sl):
            continue
        # 仅与标题词做对比（避免描述自我比较导致overlap过高）
        tw = title_words if title_words is not None else set(w for w in tl.split() if len(w) > 4)
        sent_words = [w for w in sl.split() if len(w) > 4]
        if tw and sent_words:
            overlap = sum(1 for w in sent_words if w in tw)
            if overlap / len(sent_words) > 0.6:
                continue
        return s[:200]
    return ''


def generate_summary_line(a):
    title = a.get('title', '') or ''
    desc = a.get('description', '') or ''
    tl = (title + ' ' + desc).lower()
    # 预计算标题词集合（用于overlap检测，避免描述自我比较）
    title_words = set(w for w in title.lower().split() if len(w) > 4)

    # 融资事件
    if any(k in tl for k in ['raise', 'funding', 'raised', 'secured', 'investment of']):
        amounts = _extract_funding_amount(title + ' ' + desc)
        companies = a.get('_company', [])
        company = (companies[0] if isinstance(companies, list) and companies
                   else (companies or ''))
        if not company:
            for name in TIER1_COMPANIES | TIER2_COMPANIES:
                if name.lower() in tl:
                    company = name
                    break
        if amounts:
            amt = amounts[0]
            amt_str = f'${amt/1e9:.1f}B' if amt >= 1e9 else f'${amt/1e6:.0f}M'
            base = f'{company} 获得 {amt_str} 融资' if company else f'某AI公司获 {amt_str} 融资'
        else:
            base = f'{company} 完成新一轮融资' if company else 'AI公司完成新一轮融资'
        sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
        return (base + '：' + sent) if sent else base + '。'

    # 模型发布
    model_kw = ['gpt-', 'claude', 'gemini', 'llama', 'mistral', 'deepseek', ' o3', ' o4', 'r1']
    for kw in model_kw:
        if kw in tl:
            for name, keywords in COMPANY_MAP.items():
                if any(k in tl for k in keywords):
                    sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
                    if sent:
                        return f'{name} 发布新一代AI模型：{sent}'
                    if len(title) > 15:
                        return title.rstrip('.。') + '。'
                    return f'{name} 发布新一代AI模型。'
            sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
            return ('头部AI公司发布新一代模型：' + sent) if sent else '头部AI公司发布新一代模型。'

    # 政策监管
    if any(k in tl for k in ['regulation', 'ban', 'antitrust', 'congress', 'eu ai act', 'policy', 'veto']):
        sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
        if 'china' in tl or 'chinese' in tl:
            base = '中国AI监管/出口管制政策有新动向'
        elif 'eu ' in tl or 'europe' in tl:
            base = '欧盟AI监管政策有新进展'
        elif 'trump' in tl or 'executive order' in tl:
            base = '美国政府出台AI相关行政令'
        else:
            base = 'AI行业迎来重大监管政策变动'
        return (base + '：' + sent) if sent else base + '。'

    # 基础设施
    if any(k in tl for k in ['data center', 'stargate', 'infrastructure', 'gpu cluster']):
        sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
        base = 'AI基础设施领域有大额投资或合作公告'
        return (base + '：' + sent) if sent else base + '。'
    if 'jensen huang' in tl or 'nvidia announce' in tl:
        sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
        base = 'Nvidia 发布新一代AI芯片或平台'
        return (base + '：' + sent) if sent else base + '。'

    # 安全泄露
    if any(k in tl for k in ['breach', 'hack', 'leak', 'data leak', 'security']):
        sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
        base = 'AI公司发生安全泄露或数据事件'
        return (base + '：' + sent) if sent else base + '。'

    # 高管变动
    if any(k in tl for k in ['resign', 'departure', 'fired', 'ceo', 'founder departure']):
        sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
        base = 'AI公司高管发生重大人事变动'
        return (base + '：' + sent) if sent else base + '。'

    # 默认：取描述中一句完整句子（仅与标题对比overlap）
    sent = _clean_sentence(_extract_sentence(desc, tl, title_words))
    if sent:
        return sent
    # 最后用完整标题，去除RSS噪声
    title_clean = re.sub(r'\s*[-–—]\s*The post.*$', '', title, flags=re.IGNORECASE).strip()
    return title_clean.rstrip('.。') + '。' if title_clean else (desc[:120].strip().rstrip('.。') + '。')




    if not desc:
        return ''
    # 排除 RSS 来源归属噪声句式
    NOISE_PREFIXES = (
        'the post ', 'originally published at', 'read more at', 'copyright ',
        'via ', 'image:', 'image credit:', 'disclosure:', 'sponsored',
        'follow us on', 'subscribe to', 'sign up for', 'newsletter',
        'appeared first on', 'you might also like', 'related articles',
        'advertisement', 'sponsored content', 'partner content',
        '文章轉載', '轉載自', '來源：', '原文連結', '未經授權',
    )
    sentences = re.split(r'[\n\r]+|[.!?。！？]', desc)
    for s in sentences:
        s = s.strip()
        sl = s.lower()
        if len(s) < 20:
            continue
        if any(sl.startswith(p) for p in NOISE_PREFIXES):
            continue
        if re.search(r'https?://|www\.', sl):
            continue
        # 排除与标题核心词高度重复的内容（超过 60% 词重叠则跳过）
        overlap = sum(1 for w in sl.split() if w in tl and len(w) > 4)
        if overlap / max(len(sl.split()), 1) > 0.6:
            continue
        return s[:200]
    return ''


def _normalize_summary_key(line, article):
    """去重key：摘要前40字符（保留动作细节）+ 公司名"""
    companies = article.get('_company', [])
    if isinstance(companies, list) and companies:
        company = companies[0]
    elif companies:
        company = companies
    else:
        tl = (article.get('title', '') + ' ' + article.get('description', '')).lower()
        for name in TIER1_COMPANIES | TIER2_COMPANIES:
            if name.lower() in tl:
                company = name
                break
        else:
            company = ''
    return line[:40].strip() + '|' + company


def build_executive_summary(articles):
    top = _get_top_articles(articles, n=50)  # 取更多候选
    if not top:
        return ''

    selected = []  # [(line, score, article)]
    # 按重要性得分从高到低处理，分数相同则时间最新的优先
    # 使用 (score, timestamp) 复合键：分数高的优先，分数相同时时间戳大的（更新）优先
    def _sort_key(a):
        ts = a.get('publishedAt', '')
        try:
            dt = __import__('datetime').datetime.fromisoformat(ts.replace('Z', '+00:00'))
            numeric_ts = dt.timestamp()
        except Exception:
            numeric_ts = 0
        return (get_importance_score(a['title'], a['description'], a['source']), numeric_ts)
    top.sort(key=_sort_key, reverse=True)

    for a in top:
        if len(selected) >= 5:
            break
        score = get_importance_score(a['title'], a['description'], a['source'])
        if score == 0:
            continue
        line = generate_summary_line(a)
        # 与所有已选条目逐一比较 BOW 相似度，超过 50% 即为重复事件，跳过
        if any(_bow_sim(line, prev_line) >= 0.5 for prev_line, _, _ in selected):
            continue
        selected.append((line, score, a))

    items = ''
    for idx, (line, _, a) in enumerate(selected, 1):
        num = str(idx)
        date_str = _format_date_short(a.get('publishedAt', ''))
        date_html = f'<span class="es-date">{date_str}</span>' if date_str else ''
        imp = a.get('_important', False)
        imp_cls = ' es-item-important' if imp else ''
        imp_num_cls = ' es-num-important' if imp else ''
        url = a.get('url', '') or ''
        if url:
            items += (
                f'<div class="es-item{imp_cls}">'
                f'<span class="es-num{imp_num_cls}">{num}</span>'
                f'<a class="es-text" href="{esc(url)}" target="_blank" rel="noopener">{line}</a>'
                f'{date_html}'
                f'</div>'
            )
        else:
            items += (
                f'<div class="es-item{imp_cls}">'
                f'<span class="es-num{imp_num_cls}">{num}</span>'
                f'<span class="es-text">{line}</span>'
                f'{date_html}'
                f'</div>'
            )

    return (
        '<div class="exec-summary">'
        '<div class="exec-summary-title">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
        '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>'
        '<line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
        '高管速读 &middot; 今日核心事件'
        '</div>'
        + items +
        '</div>'
    )

COMPANY_MAP = {

    'OpenAI':          ['openai', 'chatgpt', 'sam altman', 'open ai'],

    'Anthropic':       ['anthropic', 'claude ai', 'claude model', 'dario amend'],

    'Google':          ['google ai', 'deepmind', 'gemini', 'alphabet', "google's ai", 'google ai'],

    'Meta':            ['meta ai', 'llama', 'meta platforms', 'mark zuckerberg', 'zuck'],

    'Microsoft':       ['microsoft', 'openai partnership', 'copilot', 'azure ai', 'satya nadella'],

    'Amazon':          ['amazon ai', 'aws ai', 'alexa', 'anthropic investment', 'bedrock'],

    'Nvidia':          ['nvidia', 'gpu', 'blackwell', 'h100', 'jensen huang', 'cuda'],

    'xAI':             ['xai', 'grok', 'elon musk ai', 'musk ai'],

    'Mistral':         ['mistral ai', 'mistral'],

    'Perplexity':      ['perplexity', 'perplexity ai'],

    'Scale AI':        ['scale ai'],

    'Cohere':          ['cohere ai', 'cohere'],

    'Character.AI':    ['character ai', 'character.ai'],

    'Midjourney':      ['midjourney'],

    'Stability AI':    ['stability ai'],

    'Runway':          ['runway ai', 'runway ml'],

    'Adept':           ['adept ai'],

    'Inflection':      ['inflection ai', 'pi ai'],

    'Databricks':      ['databricks', 'mosaicml'],

    'Hugging Face':    ['hugging face', 'huggingface'],

    'Figure AI':       ['figure ai', 'figure robot'],

    '1X Technologies': ['1x technologies', '1x tech', 'neo robot'],

    'Tesla':           ['tesla', 'elon musk', 'autopilot', 'optimus'],

    'Apple':           ['apple ai', 'apple intelligence', 'siri', 'wwdc'],

    'Samsung':         ['samsung ai', 'galaxy ai'],

    'SoftBank':        ['softbank', 'masayoshi son', 'vision fund'],

    'Sequoia':         ['sequoia capital', 'sequoia vc'],

    'a16z':            ['a16z', 'andreessen horowitz'],

    'DeepSeek':        ['deepseek', 'deep seek'],

}





def get_tags(title, desc):

    tl = (title + ' ' + desc).lower()

    matched = []

    for tag_name, keywords in TAG_RULES:

        if any(k in tl for k in keywords):

            matched.append(tag_name)

        if len(matched) >= 3:

            break

    return matched if matched else ['AI模型与技术']





def get_article_companies(title, desc):

    tl = (title + ' ' + desc).lower()

    matched = [name for name, keywords in COMPANY_MAP.items()

               if any(k in tl for k in keywords)]

    return matched





def _get_company_counts(articles):

    counts = {}

    for name, keywords in COMPANY_MAP.items():

        kl = [k.lower() for k in keywords]

        cnt = sum(

            1 for a in articles

            if any(k in (a.get('title', '') + ' ' + a.get('description', '')).lower() for k in kl)

        )

        if cnt > 0:

            counts[name] = cnt

    # 同时计算实际出现在卡片上的公司

    for a in articles:

        companies = a.get('_company', [])

        if isinstance(companies, list):

            for c in companies:

                counts[c] = counts.get(c, 0) + 0  # already counted above

    return counts





def truncate(text, max_len=150):

    if len(text) > max_len:

        return text[:max_len-3] + '...'

    return text





def _format_time(publishedAt, date):
    """显示UTC原始报道时间（date字段本身已是UTC日期转CST后之日）"""
    if publishedAt and 'T' in str(publishedAt):
        try:
            return date[5:]  # 显示 news_raw.json 中 date 字段的月日部分（已为CST日期）
        except Exception:
            return date[5:]
    return date[5:]





def esc(s):

    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'", '&#39;')





def build_card(a):

    tags_html = ''.join(

        '<span class="tag" style="background:' + TAGS[t] + '22;color:' + TAGS[t] + '">' + t + '</span>'

        for t in a['_tags']

    )

    data_tags = ' '.join(a['_tags'])

    companies = a.get('_company', [])

    if isinstance(companies, str):

        companies = [companies] if companies else []

    company = companies[0] if companies else ''

    company_all = ' '.join(companies)  # space-separated for filtering

    desc = truncate(a.get('description', ''))

    is_important = a.get('_important', False)

    important_badge = '<span class="important-badge">重要</span>' if is_important else ''

    company_badge = '<span class="company-badge">' + esc(company) + '</span>' if company else ''

    card_cls = 'card card-important' if is_important else 'card'

    data_important = ' data-important="1"' if is_important else ''

    data_company = ' data-company="' + esc(company_all) + '"' if company_all else ''

    time_display = _format_time(a.get('publishedAt', ''), a['date'])

    return (

        '<div class="' + card_cls + '" data-tags="' + data_tags + '" data-date="' + a['date'] + '"' + data_company + data_important + '>'

        '<div class="card-header">'

        '<span class="card-source">' + esc(a['source']) + '</span>'

        '<span class="card-time">' + important_badge + company_badge + time_display + '</span>'

        '</div>'

        '<h3>' + esc(a['title']) + '</h3>'

        '<p class="card-summary">' + esc(desc) + '</p>'

        '<div class="card-footer">'

        '<a class="card-link" href="' + esc(a['url']) + '" target="_blank">Read More</a>'

        '<div class="card-tags">' + tags_html + '</div>'

        '</div></div>'

    )





def generate_html(articles, today_str):

    for a in articles:

        a['_tags'] = get_tags(a['title'], a['description'])

        a['_important'] = is_important(a['title'], a['description'], a['source'])

        a['_company'] = get_article_companies(a['title'], a['description'])



    articles.sort(key=lambda x: x['publishedAt'], reverse=True)

    total = len(articles)

    important_total = sum(1 for a in articles if a.get('_important'))

    tag_counts = {t: sum(1 for a in articles if t in a['_tags']) for t in TAGS}

    # 从实际分配结果计算公司文章数

    actual_company_counts = {}

    for a in articles:

        for c in a.get('_company', []):

            actual_company_counts[c] = actual_company_counts.get(c, 0) + 1

    company_counts = actual_company_counts

    cards_html = ''.join(build_card(a) for a in articles)



    # 预构建标签chips JS

    chip_snippets = []

    for tag, color in TAGS.items():

        cnt = tag_counts[tag]

        chip_snippets.append(

            'var chip=document.createElement("button");'

            'chip.className="summary-chip"+(cur=="' + tag + '"?" active":"");'

            'chip.style.background=cur=="' + tag + '"?"' + color + '":"' + color + '22";'

            'chip.style.color=cur=="' + tag + '"?"#fff":"' + color + '";'

            'chip.style.border="1px solid ' + color + '55";'

            'chip.textContent="' + tag + ' ' + str(cnt) + '";'

            'chip.onclick=function(){filter("' + tag + '");};'

            'bar.appendChild(chip);'

        )

    chips_block = '\n    '.join(chip_snippets)



    # 预构建公司快捷按钮JS

    top_companies = sorted(company_counts.items(), key=lambda x: -x[1])[:10]

    company_chips_js = ''

    for name, cnt in top_companies:

        name_esc = name.replace('"', '\\"')

        company_chips_js += (

            'var b=document.createElement("button");'

            'b.className="company-chip";'

            'b.setAttribute("data-company","' + name_esc + '");'

            'b.innerHTML="' + name_esc + ' <span style=\\"opacity:0.6\\">x' + str(cnt) + '</span>";'

            'b.onclick=function(){'

            '  var c=this.getAttribute("data-company");'

            '  curCompany=(curCompany===c?"":c);'

            '  document.querySelectorAll(".company-chip").forEach(function(x){x.classList.remove("active");});'

            '  if(curCompany)this.classList.add("active");'

            '  applyFilter();'

            '};'

            'document.getElementById("company-chips").appendChild(b);'

        )



    total_str = str(total)

    important_str = str(important_total)

    today_date = today_str

    js_code = (

        'var cur="全部";'

        'var curCompany="";'

        'var searchText="";'

        'var curImportant=false;'

        'var curToday=false;'

        'var todayDate="' + today_date + '";'

        'var allCards=document.querySelectorAll(".card");'

        'var countEl=document.getElementById("art-count");'

        + company_chips_js + ';'

        'var searchInput=document.getElementById("search-input");'

        'searchInput.addEventListener("input",function(){'

        '  searchText=searchInput.value.trim().toLowerCase();'

        '  applyFilter();'

        '});'

        'function toggleImportant(){'

        '  curImportant=!curImportant;'

        '  if(curImportant){curToday=false;document.getElementById("btn-today").classList.remove("active-today");}'

        '  var btn=document.getElementById("btn-important");'

        '  btn.classList.toggle("active-important",curImportant);'

        '  applyFilter();'

        '}'

        'function toggleToday(){'

        '  curToday=!curToday;'

        '  if(curToday){curImportant=false;document.getElementById("btn-important").classList.remove("active-important");}'

        '  var btn=document.getElementById("btn-today");'

        '  btn.classList.toggle("active-today",curToday);'

        '  applyFilter();'

        '}'

        'function applyFilter(){'

        '  var visible=0;'

        '  allCards.forEach(function(c){'

        '    var ts=c.getAttribute("data-tags").split(" ");'

        '    var co=c.getAttribute("data-company")||"";'

        '    var imp=c.getAttribute("data-important");'

        '    var d=c.getAttribute("data-date")||"";'

        '    var ti=c.querySelector("h3")?c.querySelector("h3").textContent.toLowerCase():" ";'

        '    var matchTag=(cur==="全部"||ts.indexOf(cur)>-1);'

        '    var matchCo=(curCompany===""||co.split(" ").indexOf(curCompany)>-1);'

        '    var matchSearch=(searchText===""||ti.indexOf(searchText)>-1||co.toLowerCase().indexOf(searchText)>-1);'

        '    var matchImp=(!curImportant||imp==="1");'

        '    var matchToday=(!curToday||d===todayDate);'

        '    c.style.display=(matchTag&&matchCo&&matchSearch&&matchImp&&matchToday)?"":"none";'

        '    if(c.style.display!=="none")visible++;'

        '  });'

        '  countEl.textContent=visible+" / ' + total_str + ' articles";'

        '  renderChips();'

        '}'

        'function renderChips(){'

        '  var bar=document.getElementById("summary");'

        '  bar.innerHTML="";'

        '  var all=document.createElement("button");'

        '  all.className="summary-chip"+(cur==="全部"?" active":"");'

        '  all.style.background=cur==="全部"?"#6366f1":"rgba(99,102,241,0.15)";'

        '  all.style.color=cur==="全部"?"#fff":"#8892a4";'

        '  all.style.border=cur==="全部"?"1px solid #6366f1":"1px solid rgba(255,255,255,0.1)";'

        '  all.textContent="全部 ' + total_str + '";'

        '  all.onclick=function(){cur="全部";applyFilter();};'

        '  bar.appendChild(all);'

        '  ' + chips_block + ';'

        '}'

        'function filter(tag){'

        '  cur=tag;'

        '  applyFilter();'

        '}'

        'countEl.textContent="' + total_str + ' / ' + total_str + ' articles";'

        'renderChips();'

    )



    html = (

        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'

        '<meta charset="UTF-8">\n'

        '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'

        '<title>AI Daily -- ' + today_str + '</title>\n'

        '<style>\n'

        '*{margin:0;padding:0;box-sizing:border-box;}\n'

        'body{background:#0a0a1a;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;'

        'min-height:100vh;padding:40px 20px;color:#e0e6f0;}\n'

        '.header{text-align:center;margin-bottom:40px;}\n'

        '.badge{display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);'

        'color:white;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;'

        'padding:4px 12px;border-radius:20px;margin-bottom:12px;}\n'

        'h1{font-size:28px;font-weight:700;color:#fff;margin-bottom:6px;}\n'

        '.subtitle{font-size:13px;color:#8892a4;margin-bottom:6px;}\n'

        '.note{text-align:center;font-size:12px;color:#4b5563;margin-bottom:30px;}\n'

        '.search-bar{max-width:1200px;margin:0 auto 24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;}\n'

        '.search-wrap{position:relative;flex:1;min-width:200px;max-width:360px;}\n'

        '.search-input{width:100%;background:rgba(255,255,255,0.05);border:1px solid rgba(99,102,241,0.3);'

        'border-radius:12px;padding:8px 16px 8px 36px;color:#e0e6f0;font-size:13px;outline:none;}\n'

        '.search-input:focus{border-color:#6366f1;background:rgba(99,102,241,0.1);}\n'

        '.search-input::placeholder{color:#6b7280;}\n'

        '.search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);'

        'color:#6b7280;font-size:14px;}\n'

        '.company-chips{display:flex;flex-wrap:wrap;gap:6px;}\n'

        '.company-chip{font-size:11px;padding:4px 12px;border-radius:16px;cursor:pointer;'

        'transition:all 0.15s;background:rgba(255,255,255,0.05);'

        'border:1px solid rgba(255,255,255,0.1);color:#9ca3af;}\n'

        '.company-chip:hover{border-color:rgba(99,102,241,0.5);color:#e0e6f0;}\n'

        '.company-chip.active{background:rgba(99,102,241,0.2);border-color:#6366f1;color:#a5b4fc;}\n'

        '.summary-bar{max-width:1200px;margin:0 auto 36px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center;}\n'

        '.summary-chip{font-size:12px;padding:5px 14px;border-radius:20px;font-weight:600;cursor:pointer;'

        'display:inline-block;transition:all 0.15s;}\n'

        '.summary-chip.active{transform:scale(1.05);}\n'

        '.quick-filter{display:flex;gap:8px;justify-content:center;margin-bottom:20px;}\n'

        '.quick-btn{font-size:12px;padding:6px 16px;border-radius:20px;cursor:pointer;'

        'font-weight:600;transition:all 0.15s;border:1px solid rgba(255,255,255,0.1);'

        'background:rgba(255,255,255,0.05);color:#9ca3af;}\n'

        '.quick-btn:hover{border-color:rgba(99,102,241,0.4);color:#e0e6f0;}\n'

        '.quick-btn.active-important{background:rgba(255,80,80,0.15);'

        'border-color:rgba(255,80,80,0.5);color:#ff8a8a;}\n'

        '.quick-btn.active-today{background:rgba(34,197,94,0.15);'

        'border-color:rgba(34,197,94,0.5);color:#4ade80;}\n'

        '.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));'

        'gap:20px;max-width:1200px;margin:0 auto;}\n'

        '.card{background:linear-gradient(145deg,#111827,#1a1f35);'

        'border:1px solid rgba(99,102,241,0.15);border-radius:16px;padding:24px;}\n'

        '.card-important{background:linear-gradient(145deg,#1a1f35,#2a1f25);'

        'border:1px solid rgba(255,80,80,0.4);border-radius:16px;padding:24px;'

        'box-shadow:0 0 20px rgba(255,80,80,0.08);}\n'

        '.card-important h3{color:#ff8a8a !important;}\n'

        '.important-badge{display:inline-block;background:#ff4d4d;color:#fff;'

        'font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;margin-right:6px;'

        'letter-spacing:1px;vertical-align:middle;}\n'

        '.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}\n'

        '.card-source{font-size:11px;color:#6366f1;font-weight:600;letter-spacing:0.5px;}\n'

        '.card-time{font-size:11px;color:#4b5563;}\n'

        '.card h3{font-size:15px;font-weight:600;color:#f3f4f6;line-height:1.5;margin-bottom:10px;}\n'

        '.card-summary{font-size:13px;color:#9ca3af;line-height:1.7;margin-bottom:14px;}\n'

        '.card-footer{display:flex;align-items:center;justify-content:space-between;gap:8px;}\n'

        '.card-link{font-size:12px;color:#6366f1;white-space:nowrap;flex-shrink:0;}\n'

        '.card-tags{display:flex;flex-wrap:wrap;gap:5px;justify-content:flex-end;}\n'

        '.tag{font-size:11px;padding:2px 8px;border-radius:12px;white-space:nowrap;}\n'

        '.company-badge{display:inline-block;background:rgba(99,102,241,0.2);color:#a5b4fc;'

        'font-size:10px;font-weight:600;padding:2px 8px;border-radius:10px;margin-right:8px;}\n'

        '.footer{text-align:center;margin-top:60px;font-size:12px;color:#4b5563;padding-bottom:40px;}\n'

        '.exec-summary{max-width:1200px;margin:0 auto 40px;background:linear-gradient(135deg,#1a1f35,#111827);'

        'border:1px solid rgba(99,102,241,0.25);border-radius:16px;padding:24px 28px;}\n'

        '.exec-summary-title{display:flex;align-items:center;gap:8px;font-size:12px;'

        'font-weight:700;color:#6366f1;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:18px;}\n'

        '.es-item{display:flex;align-items:flex-start;gap:14px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);}\n'

        '.es-item:last-child{border-bottom:none;padding-bottom:0;}\n'

        '.es-item-important{background:rgba(255,80,80,0.04);border-radius:8px;padding:10px 12px !important;margin-bottom:4px;border:none !important;}\n'

        '.es-num{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;'

        'border-radius:50%;background:rgba(99,102,241,0.2);color:#a5b4fc;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px;}\n'

        '.es-num-important{background:rgba(255,80,80,0.2);color:#ff8a8a;}\n'

        '.es-text{font-size:13px;color:#e0e6f0;line-height:1.6;flex:1;word-break:break-word;white-space:normal;max-width:none;overflow:visible;}\n'

        '.es-text a{color:#e0e6f0;text-decoration:none;transition:color 0.15s;}\n'

        '.es-text a:hover{color:#818cf8;text-decoration:underline;}\n'

        '.es-item-important .es-text{color:#f3f4f6;}\n'

        '.es-item-important .es-text a:hover{color:#f8b4b4;}\n'

        '.es-date{font-size:11px;color:#4b5563;margin-left:auto;flex-shrink:0;padding-top:2px;}\n'

        '@media(max-width:600px){'

        '.cards-grid{grid-template-columns:1fr;}'

        '.card-footer{flex-direction:column-reverse;align-items:flex-start;}'

        '.exec-summary{padding:16px 18px;}'

        '}\n'

        '</style>\n</head>\n<body>\n'

        '<div class="header">\n'

        '<div class="badge">DAILY BRIEF</div>\n'

        '<h1>AI Daily -- ' + today_str + '</h1>\n'

        '<div class="subtitle">Real-time &middot; AI Industry News Last 30 Days</div>\n'

        '</div>\n'

        '<p class="note" id="art-count"></p>\n'

        + build_executive_summary(articles) + '\n'

        '<div class="search-bar">\n'

        '<div class="search-wrap">\n'

        '<span class="search-icon">&#128269;</span>\n'

        '<input class="search-input" id="search-input" type="text" placeholder="搜索公司 / Search company...">\n'

        '</div>\n'

        '<div class="company-chips" id="company-chips"></div>\n'

        '</div>\n'

        '<div class="quick-filter">\n'

        '<button class="quick-btn" id="btn-important" onclick="toggleImportant()">只看重点 ' + str(important_total) + '</button>\n'

        '<button class="quick-btn" id="btn-today" onclick="toggleToday()">只看今日 ' + str(sum(1 for a in articles if a['date'] == today_str)) + '</button>\n'

        '</div>\n'

        '<div class="summary-bar" id="summary"></div>\n'

        '<div class="cards-grid" id="card-grid">' + cards_html + '</div>\n'

        '<div class="footer">AI-Daily &middot; Source: NewsAPI (TechCrunch / The Verge / Wired / CNBC) &middot; ' + today_str + '</div>\n'

        '<script>\n' + js_code + '\n</script>\n'

        '</body>\n</html>'

    )

    return html





def main():

    json_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'news_raw.json')

    if not os.path.exists(json_path):

        print('[ERROR] news_raw.json not found at', json_path)

        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:

        articles = json.load(f)



    today = datetime.now()

    today_file = today.strftime('%Y%m%d')

    today_display = today.strftime('%Y-%m-%d')



    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    out_path = os.path.join(out_dir, 'AI报-' + today_file + '.html')



    html = generate_html(articles, today_display)

    with open(out_path, 'w', encoding='utf-8') as f:

        f.write(html)



    tag_counts = {t: sum(1 for a in articles if t in a['_tags']) for t in TAGS}

    important_total = sum(1 for a in articles if a.get('_important'))

    company_counts = _get_company_counts(articles)



    print('[OK] Saved to:', out_path)

    print('[INFO] Total:', len(articles), 'articles | Important:', important_total)

    for t, c in sorted(tag_counts.items(), key=lambda x: -x[1]):

        print('  ', t + ':', c)

    print('[INFO] Company distribution:')

    for name, cnt in sorted(company_counts.items(), key=lambda x: -x[1]):

        print('  ', name + ':', cnt)





if __name__ == '__main__':

    main()