# AI-Daily · 每日AI资讯日报

为 Claude Code 打造的每日AI行业资讯技能，联网抓取近30天真实新闻，生成精美HTML卡片界面。

---

## 功能特性

- **实时资讯**：自动抓取近30天AI行业新闻（来源：TechCrunch、The Verge、Wired、Ars Technica等）
- **智能分类**：每条新闻自动打上1-3个专业标签
- **筛选导航**：顶部标签按钮，点击即可筛选对应类别
- **公司追踪**：自动识别新闻涉及的公司（OpenAI、Google、Nvidia等）
- **重点标记**：重要新闻（融资/监管/大模型发布）自动标红突出
- **双语支持**：生成英文页面，用Edge浏览器一键翻译为中文

---

## 安装

### 方式一：Git 克隆（推荐）

```bash
git clone https://github.com/Lisa-wmy/JOB-SKILL.git ~/.claude/skills/ai-daily
```

### 方式二：手动下载

下载整个仓库，将文件夹重命名为 `ai-daily`，放入 Claude Code 的 skills 目录：
```
~/.claude/skills/ai-daily/
```

---

## 配置 NewsAPI Key

1. 访问 https://newsapi.org 注册免费账号
2. 获取你的 API Key
3. 使用技能时，Claude Code 会自动询问你输入 Key

---

## 使用方法

在 Claude Code 中直接说：

```
AI日报
AI资讯
今日AI动态
AI行业动态
```

Claude Code 会自动引导你完成以下三步：

1. **询问 NewsAPI Key**（首次使用时）
2. **运行抓取脚本**：下载近30天AI新闻
3. **运行生成脚本**：输出精美HTML日报

生成文件为 `AI日报-YYYYMMDD.html`，用浏览器打开即可阅读。

---

## 新闻标签体系

| 标签 | 说明 |
|------|------|
| AI模型与技术 | 大模型发布、benchmark、研究突破 |
| AI基础设施 | 数据中心、GPU、芯片、云服务 |
| AI融资与估值 | 融资轮次、IPO、公司估值 |
| AI政策与监管 | 各国AI法规、反垄断、政府政策 |
| AI商业应用 | 机器人、自动驾驶、医疗、企业软件 |
| AI安全伦理 | 数据泄露、隐私、深度伪造、伦理风险 |

---

## 文件说明

```
├── skill.md           # 技能定义文件（Claude Code 读取）
├── scripts/
│   ├── fetch_news.py  # 新闻抓取脚本（NewsAPI + RSS）
│   └── gen_daily.py   # HTML日报生成脚本
└── evals/
    └── evals.json     # 评测配置
```

---

## 环境要求

- Python 3.8+
- `requests` 库
- （可选）`feedparser` 库，用于RSS订阅

```bash
pip install requests feedparser
```

---

## 翻译为中文

生成的是英文页面。用 **Edge 浏览器**打开 `AI日报-YYYYMMDD.html`，点击地址栏右侧的翻译图标，一键翻译全页。

---

## 授权

MIT License · 欢迎自由使用、修改和分享