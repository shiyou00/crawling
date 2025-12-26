# 新闻采集系统 - 最终部署说明

## ✅ 系统状态

**已完成并测试的功能：**

1. ✅ 虚拟环境配置完成（所有依赖已安装）
2. ✅ **Science Daily 爬虫 - 已优化！采集物质与能源分类，覆盖量子物理和其他物理新闻**
3. ✅ **Buffalo University 爬虫 - 已修复！可以正确提取日期和新闻**
4. ✅ **IQM 爬虫 - 已修复！可以正确提取日期和新闻**
5. ✅ **翻译功能** - 使用 Google Translate API 将英文翻译为中文
6. ✅ **内容摘要** - 自动获取新闻全文并生成摘要

## 🎯 已验证的功能

**✅ Science Daily 爬虫测试（2025-12-26 重大修复）：**
```bash
python main.py --date 2025-12-06
python main.py --date 2025-12-19
```
- 采集源：`https://www.sciencedaily.com/news/matter_energy/quantum_physics/`（量子物理分类）
- **日期提取方式**：从页面显示的 `<span class="story-date">` 元素提取（如 "Dec. 6, 2025"）
- **HTML 结构**：
  - 新闻容器：`div.col-md-6`
  - 标题：`div.latest-head > a`
  - 日期：`div.latest-summary > span.story-date`
- ✅ **已修复**：现在可以正确采集页面上显示的日期，而不是从 URL 中提取
- ✅ 测试验证：成功采集 12-06、12-13、12-19 等日期的新闻

**✅ IQM 爬虫测试（2025-12-26 修复）：**
```bash
python main.py --date 2025-12-10
```
- 成功采集到 1 条 IQM 的新闻
- 日期格式：`10 Dec` 或 `14 Nov 2025` (DD Mon 或 DD Mon YYYY)
- HTML 结构：`div[class*="press"]` (新闻列表), `div.elementor` (正文内容)

**✅ Buffalo University 爬虫测试（2025-12-26 修复）：**
```bash
python main.py --date 2025-12-22
```
- 成功采集到 2 条 Buffalo University 的新闻
- 日期格式：`12/22/25` (MM/DD/YY)
- HTML 结构：`div.teaser-title > span` (标题), `span.teaser-date` (日期)

**输出结果：**
- JSON 文件保存在 `output/news_20251222.json`
- ✅ **完整新闻内容** - 系统会自动跳转到每条新闻详细页面爬取全文
- ✅ 包含 `full_content` 字段（新闻完整正文，3000+ 字符）
- ✅ 包含 `summary` 字段（自动生成的英文摘要）
- ✅ 包含 `title_zh` 和 `summary_zh`（中文翻译）
- ✅ 包含新闻标题、日期、链接等基本信息

### 📰 新闻内容采集功能

**✅ 系统现在会自动跳转到每条新闻的详细页面，爬取完整内容！**

**支持的网站内容提取：**
1. **Buffalo University**：从 `div.text.parbase.section` 提取所有段落
2. **Science Daily**：从 `div#text` 提取所有段落
3. **IQM**：从 `article` 或 `div.entry-content` 提取段落

**JSON 输出字段说明：**
```json
{
  "title": "新闻标题",
  "title_zh": "中文标题",
  "full_content": "完整新闻正文（所有段落）",
  "summary": "自动生成的英文摘要（前3句）",
  "summary_zh": "中文摘要",
  "date": "2025-12-22",
  "link": "https://..."
}
```

## 📝 重要说明

### 关于采集结果为空

如果采集某个日期的新闻结果为 0，可能的原因：

1. **节假日** - 如 12 月 25 日（圣诞节），网站可能不发布新闻
2. **周末** - 某些网站周末不更新
3. **时区差异** - 网站发布时间可能与您的本地时间有差异
4. **网站结构** - Buffalo 和 IQM 的日期信息位置需要进一步调试

### 当前可用功能

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试系统
python test.py

# 采集指定日期的新闻（带翻译和摘要）
python main.py --date 2025-11-24
python main.py --date 2025-12-23

# 采集昨天的新闻（默认，包含翻译和摘要）
python main.py

# 禁用翻译功能（仅采集原文）
python main.py --no-translate

# 禁用摘要功能（不获取全文）
python main.py --no-summary

# 同时禁用翻译和摘要
python main.py --no-translate --no-summary

# 只查看结果不保存
python main.py --no-save

# 查看帮助
python main.py --help
```

## 🌐 翻译和摘要功能

### 翻译功能
- **翻译引擎**：Google Translate API（免费）
- **翻译方向**：英文 → 简体中文
- **翻译内容**：标题 (`title_zh`) 和摘要 (`summary_zh`)
- **自动重试**：失败时自动重试 3 次
- **备用方案**：如果翻译失败，保留原文

### 内容摘要
- **自动获取**：从新闻链接获取完整正文内容
- **智能提取**：根据不同网站结构提取正文
- **摘要生成**：自动提取前 3 个关键句子作为摘要
- **全文保存**：完整内容保存在 `full_content` 字段（可选）

### JSON 输出格式示例

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
      "title": "This Glowing Particle...",
      "title_zh": "这个发光粒子...",
      "summary": "Scientists have discovered...",
      "summary_zh": "科学家们发现了...",
      "full_content": "完整正文内容...",
      "date": "2025-11-24",
      "link": "https://..."
    }
  ]
}

## 🔧 下一步优化建议

如果您需要 Buffalo 和 IQM 也能正常工作，可以：

1. **运行调试脚本** 查看实际的 HTML 结构：
   ```bash
   python debug_detail.py
   ```

2. **针对性调整** 每个爬虫的日期提取逻辑

3. **测试最近的日期** 找到网站实际有新闻发布的日期

## 📊 查看采集结果

采集结果保存在 `output/` 目录：

```bash
# 查看最新的采集结果
cat output/news_*.json | jq .

# 或使用 Python 查看
python -m json.tool output/news_20251124.json
```

## 🚀 生产环境部署

当您确认系统工作正常后，可以设置定时任务：

```bash
# 每天凌晨 2 点自动采集
python scheduler.py

# 自定义时间（如凌晨 3:30）
python scheduler.py --time 03:30

# 立即测试一次
python scheduler.py --run-now
```

## 💡 提示

- 首次使用建议先手动测试几个最近的日期
- 查看 `logs/` 目录了解详细的运行日志
- 如果某个网站长期无法采集，可能需要调整该爬虫的实现

---

**最后更新：** 2025-12-26
**系统版本：** 1.0
**Python 版本：** 3.12+
