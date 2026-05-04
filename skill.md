---
name: ai-daily
description: >
  为你精选每日AI行业资讯。适合以下场景：
  - 用户说"AI日报"、"AI资讯"、"今日AI动态"、"今日AI新闻"
  - 用户说"AI行业动态"、"国内外AI新闻"
  - 用户想了解最近AI领域的重大进展
  - 用户想看AI资讯日报
  当用户询问AI相关最新消息、想要一份AI资讯日报、或表达想了解今日AI行业动态时，激活此技能。
  不要在用户只是简单询问某个AI公司或技术概念时触发（那是知识问答，不是资讯订阅）。
triggers:
  - "AI日报"
  - "AI资讯"
  - "今日AI动态"
  - "AI行业动态"
  - "AI行业资讯"
  - "AI新闻汇总"
  - "给我看看今天的AI资讯"
keywords:
  - AI
  - 人工智能
  - 机器学习
  - 大模型
  - LLM
  - 生成式AI
  - OpenAI
  - Anthropic
  - Google AI
  - Meta AI
---

# AI-Daily: 每日AI资讯日报技能

本技能联网抓取近30天真实AI行业资讯，生成精美HTML卡片界面呈现。

## ⚙️ NewsAPI Key 设置

每次使用前，Claude Code 会询问你输入 NewsAPI Key。若 Key 失效可重新提供。

获取 Key：访问 **https://newsapi.org** 注册免费账号。

## 翻译说明

页面直接显示英文内容。**使用 Edge 浏览器打开**时，点击地址栏右侧的**翻译图标**即可一键将整个页面翻译为中文，无需在页面内嵌入翻译。

## 工作流程

### 第一步：询问用户 NewsAPI Key

每次使用时，**先询问用户是否提供 NewsAPI Key**，格式不限（Claude Code 会将其透传给脚本）。

### 第二步：运行抓取脚本

```bash
python "scripts/fetch_news.py" --key "你的KEY"
```

脚本会：
1. 从 NewsAPI 并发抓取近30天AI相关新闻（20个查询全并行，不牺牲全面性）
2. 自动过滤非AI相关内容
3. 按发布时间倒序排列
4. 保存到 `news_raw.json`（当前工作目录下）
5. 在终端打印日期分布

### 第三步：运行分类生成脚本

读取 `news_raw.json`，为每条新闻打1-3个标签，按时间倒序排列，生成带标签筛选功能的 HTML 日报。

```bash
python "scripts/gen_daily.py"
```

输出文件：`AI日报-YYYYMMDD.html`，写入当前工作目录。

---

## 新闻标签体系（专业金融分析师视角）

每条新闻打 **1-3个** 标签（命中关键词即打标，支持多标签）。顶部标签导航支持点击筛选。

| 标签 | 颜色 | 核心关键词 |
|------|--------|-----------|
| AI模型与技术 | #96CEB4 | GPT, Claude, Gemini, LLaMA, Muse, model, benchmark, research, frontier AI |
| AI基础设施 | #45B7D1 | data center, GPU, chip, Nvidia, cloud, AWS, Azure, stargate, energy |
| AI融资与估值 | #FF6B6B | raise, funding, valuation, IPO, Series A/B/C, investor, SoftBank, a16z |
| AI政策与监管 | #4ECDC4 | regulation, policy, congress, Pentagon, DOJ, Trump, antitrust, veto |
| AI商业应用 | #DDA0DD | autonomous, robot, humanoid, healthcare, legal, enterprise, copilot, agent |
| AI安全伦理 | #FF9F43 | safety, security, cyber, privacy, ethics, deepfake, vulnerability, risk |

---

## HTML日报模板规范（筛选版）

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Daily — [Date]</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0a1a; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; min-height: 100vh; padding: 40px 20px; color: #e0e6f0; }
    .header { text-align: center; margin-bottom: 40px; }
    .badge { display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; font-size: 11px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; padding: 4px 12px; border-radius: 20px; margin-bottom: 12px; }
    h1 { font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 6px; }
    .subtitle { font-size: 13px; color: #8892a4; margin-bottom: 6px; }
    .note { text-align: center; font-size: 12px; color: #4b5563; margin-bottom: 30px; }
    /* 标签导航 */
    .summary-bar { max-width: 1200px; margin: 0 auto 36px; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
    .summary-chip { font-size: 12px; padding: 5px 14px; border-radius: 20px; font-weight: 600; cursor: pointer; display: inline-block; transition: all 0.15s; }
    /* 卡片网格 */
    .cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
    .card { background: linear-gradient(145deg, #111827, #1a1f35); border: 1px solid rgba(99,102,241,0.15); border-radius: 16px; padding: 24px; }
    .card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
    .card-source { font-size: 11px; color: #6366f1; font-weight: 600; letter-spacing: 0.5px; }
    .card-time { font-size: 11px; color: #4b5563; }
    .card h3 { font-size: 15px; font-weight: 600; color: #f3f4f6; line-height: 1.5; margin-bottom: 10px; }
    .card-summary { font-size: 13px; color: #9ca3af; line-height: 1.7; margin-bottom: 14px; }
    .card-footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
    .card-link { font-size: 12px; color: #6366f1; white-space: nowrap; }
    .card-tags { display: flex; flex-wrap: wrap; gap: 5px; justify-content: flex-end; }
    .tag { font-size: 11px; padding: 2px 8px; border-radius: 12px; white-space: nowrap; }
    .footer { text-align: center; margin-top: 60px; font-size: 12px; color: #4b5563; padding-bottom: 40px; }
  </style>
</head>
<body>
  <div class="header">
    <div class="badge">DAILY BRIEF</div>
    <h1>AI Daily — [YYYY-MM-DD]</h1>
    <div class="subtitle">Real-time · AI Industry News Last 30 Days</div>
  </div>
  <p class="note" id="art-count">154 / 154 articles</p>
  <!-- 标签导航由JS动态生成 -->
  <div class="summary-bar" id="summary"></div>
  <!-- 全部卡片，时间倒序 -->
  <div class="cards-grid" id="cards">
    <div class="card" data-tags="AI模型与技术 AI融资与估值" data-date="2026-05-01">
      <div class="card-header">
        <span class="card-source">TechCrunch</span>
        <span class="card-time">2026-05-01</span>
      </div>
      <h3>[英文标题]</h3>
      <p class="card-summary">[英文摘要，150字以内]</p>
      <div class="card-footer">
        <a class="card-link" href="[真实URL]" target="_blank">Read More</a>
        <div class="card-tags">
          <span class="tag" style="background:#96CEB422;color:#96CEB4">AI模型与技术</span>
          <span class="tag" style="background:#FF6B6B22;color:#FF6B6B">AI融资与估值</span>
        </div>
      </div>
    </div>
  </div>
  <div class="footer">AI-Daily · Source: NewsAPI (TechCrunch / The Verge / Wired / CNBC) · [YYYY-MM-DD]</div>
  <script>
    // JS: 点击标签筛选卡片，顶部显示当前可见数量
    var currentTag = '全部';
    var cards = Array.from(document.querySelectorAll('.card'));
    function filter(tag) {
      currentTag = tag;
      var visible = 0;
      cards.forEach(function(c) {
        var tags = c.getAttribute('data-tags').split(' ');
        c.style.display = (tag === '全部' || tags.includes(tag)) ? '' : 'none';
        if (c.style.display !== 'none') visible++;
      });
      document.getElementById('art-count').textContent = visible + ' / ' + cards.length + ' articles';
      renderChips();
    }
    function renderChips() { /* JS动态生成立即导航按钮 */ }
    renderChips();
  </script>
</body>
</html>
```

## 内容质量标准

- **严格使用真实URL**：每张卡片的 href 必须来自 NewsAPI 实际返回的链接，禁止模拟
- **严格使用真实日期**：每张卡片右上角显示新闻实际发布时间（从 `news_raw.json` 的 `date` 字段读取）
- **按时间排序**：全部卡片按 `publishedAt` 倒序，不再按分类分块
- **多标签**：每条新闻命中关键词即打标签，支持1-3个标签（由 `gen_daily.py` 自动处理）
- **筛选功能**：顶部"全部" + 6个标签按钮，点击过滤；显示"当前可见数 / 总数"
- **选材范围**：近30天内，与 AI 直接或间接相关的行业新闻（融资、监管、产品发布、公司动态、技术突破、应用落地）
- **排除内容**：娱乐、体育、纯股票行情、非AI相关报道
- **摘要**：英文原文，150字以内，只说事实，不加评论
- **不得添加模拟内容**：没有真实数据时，只展示已获取的真实新闻，不要凭空补充

## 标签判断规则（可叠加，同时命中多个标签）

| 标签 | 核心关键词 |
|------|-----------|
| AI模型与技术 | gpt-, claude, gemini, llama, muse, model, benchmark, research, breakthrough, frontier AI, distill, openai, anthropic, deepmind |
| AI基础设施 | data center, GPU, chip, nvidia, cloud, AWS, Azure, stargate, infrastructure, energy, semiconductor |
| AI融资与估值 | raise, funding, valuation, IPO, Series A/B/C, seed round, VC, investor, SoftBank, a16z |
| AI政策与监管 | regulation, policy, congress, Pentagon, DOJ, Trump, antitrust, veto, ban, liability |
| AI商业应用 | autonomous, robot, humanoid, healthcare, legal, enterprise, copilot, agent, Tesla, GM, wearable, glasses |
| AI安全伦理 | safety, security, cyber, privacy, ethics, deepfake, vulnerability, risk, hack |

## 常见问题

**Q: 如何翻译成中文？**
A: 用 Edge 浏览器打开生成的 HTML 文件，点击地址栏右侧翻译图标即可一键翻译全页。

**Q: 朋友使用后内容不一致？**
A: 确认朋友的环境变量已设置（`$env:NEWS_API_KEY`），且 Claude Code 已重启。

**Q: 新闻数量少？**
A: 脚本已扩大搜索范围（近30天 + 12组关键词 + 更多媒体源），不再限制返回数量。