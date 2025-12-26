# 翻译和摘要功能使用指南

## 功能概述

新闻采集系统现在支持以下增强功能：

1. **自动翻译** - 使用 Google Translate API 将英文新闻翻译为中文
2. **内容摘要** - 自动获取新闻全文并生成简洁摘要

## 快速开始

### 1. 安装依赖

确保已激活虚拟环境，然后安装新的依赖：

```bash
source venv/bin/activate
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### 2. 基本使用

```bash
# 采集新闻（默认启用翻译和摘要）
python main.py --date 2025-11-24

# 禁用翻译功能
python main.py --date 2025-11-24 --no-translate

# 禁用摘要功能
python main.py --date 2025-11-24 --no-summary

# 同时禁用翻译和摘要
python main.py --date 2025-11-24 --no-translate --no-summary
```

### 3. 测试功能

```bash
# 测试翻译和摘要模块
python test_translation.py

# 运行完整演示
python demo.py
```

## 输出格式

采集的新闻将包含以下字段：

### 基本字段（始终存在）
- `source` - 新闻来源
- `title` - 英文标题
- `date` - 发布日期
- `link` - 新闻链接

### 摘要字段（启用摘要功能时）
- `summary` - 英文摘要（自动提取前 3 句关键内容）
- `full_content` - 完整新闻正文

### 翻译字段（启用翻译功能时）
- `title_zh` - 中文标题
- `summary_zh` - 中文摘要

## 示例输出

```json
{
  "date": "2025-11-24",
  "crawl_time": "2025-12-26 15:30:00",
  "total_count": 1,
  "features": {
    "translation_enabled": true,
    "summary_enabled": true
  },
  "news": [
    {
      "source": "Science Daily",
      "title": "This Glowing Particle in a Laser Trap May Reveal How Lightning Begins",
      "title_zh": "激光陷阱中的发光粒子可能揭示闪电是如何开始的",
      "date": "2025-11-24",
      "link": "https://www.sciencedaily.com/releases/2025/11/251124231904.htm",
      "summary": "Aerosols are tiny droplets or solid particles suspended in the air...",
      "summary_zh": "气溶胶是悬浮在空气中的微小液滴或固体颗粒...",
      "full_content": "完整正文内容..."
    }
  ]
}
```

## 功能说明

### 翻译功能

- **翻译引擎**: Google Translate API（免费）
- **翻译方向**: 英文 → 简体中文
- **翻译内容**: 标题和摘要
- **错误处理**:
  - 自动重试 3 次
  - 失败时保留原文
  - 每次翻译间隔 0.5 秒，避免请求过快

### 摘要功能

- **内容获取**: 自动访问新闻链接获取完整正文
- **智能提取**: 根据不同网站的 HTML 结构提取正文
  - Science Daily: 使用 `<div id="text">` 提取
  - Buffalo University: 使用 `<article>` 标签
  - IQM: 使用 `.entry-content` 类
- **摘要生成**: 提取前 3 个关键句子
- **内容保存**: 完整正文保存在 `full_content` 字段

## 性能考虑

### 处理时间

启用翻译和摘要功能后，处理时间会显著增加：

- **仅采集**: ~1-5 秒
- **采集 + 摘要**: ~5-15 秒（每条新闻 +3-5 秒）
- **采集 + 摘要 + 翻译**: ~10-30 秒（每条新闻 +5-10 秒）

### 网络要求

- 摘要功能需要访问每条新闻的链接
- 翻译功能需要访问 Google Translate API
- 建议在网络稳定的环境下运行

## 常见问题

### Q: 翻译失败怎么办？

A: 系统会自动重试 3 次。如果仍然失败，会保留原文并记录日志。您可以查看 `logs/news_crawler.log` 了解详情。

### Q: 如何只翻译标题而不翻译摘要？

A: 目前不支持单独控制。您可以修改 [translator.py](translator.py) 的 `translate_news_item` 方法。

### Q: 摘要质量如何提高？

A: 当前使用简单的提取式摘要（前 3 句）。如需更高质量的摘要，可以考虑：
- 集成 OpenAI API 使用 GPT 生成摘要
- 使用 BERT 等模型进行抽取式摘要
- 调整 [summarizer.py](summarizer.py) 中的 `max_sentences` 参数

### Q: 翻译的准确性如何？

A: 使用 Google Translate API，对于科技新闻的翻译质量较好。但专业术语可能需要人工校对。

## 模块说明

### translator.py

翻译模块，提供 `NewsTranslator` 类：

```python
from translator import NewsTranslator

translator = NewsTranslator()

# 翻译单条新闻
translated_news = translator.translate_news_item(news_item)

# 批量翻译
translated_list = translator.translate_news_list(news_list)
```

### summarizer.py

摘要模块，提供 `ContentSummarizer` 类：

```python
from summarizer import ContentSummarizer

summarizer = ContentSummarizer()

# 处理单条新闻（获取全文和摘要）
processed_news = summarizer.process_news_item(news_item)

# 批量处理
processed_list = summarizer.process_news_list(news_list)
```

## 进阶配置

### 自定义翻译语言

编辑 [translator.py](translator.py):

```python
def translate_text(self, text, src='en', dest='zh-cn', retry=3):
    # 修改 dest 参数，例如 'zh-tw' (繁体中文), 'ja' (日文) 等
```

### 调整摘要长度

编辑 [summarizer.py](summarizer.py):

```python
def generate_summary(self, content, max_sentences=3):
    # 修改 max_sentences 参数为所需的句子数量
```

### 禁用全文保存

如果不需要保存完整正文（节省存储空间），编辑 [summarizer.py](summarizer.py):

```python
def process_news_item(self, news_item, fetch_full_content=True):
    # ...
    if full_content:
        # 注释掉这一行
        # processed_item['full_content'] = full_content
```

## 日志

所有操作都会记录到 `logs/news_crawler.log`，包括：

- 翻译成功/失败
- 内容获取成功/失败
- 错误详情

查看日志：

```bash
tail -f logs/news_crawler.log
```

## 更新记录

- **2025-12-26**: 添加翻译和摘要功能
  - 使用 Google Translate API 进行翻译
  - 自动获取新闻全文并生成摘要
  - 支持通过命令行参数控制功能开关
