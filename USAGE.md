# 新闻采集系统

每天自动采集指定网站前一天发布的新闻。

## 功能特点

- 支持多个新闻源同时采集
- 自动过滤指定日期的新闻（默认采集昨天的新闻）
- 结果保存为 JSON 格式
- 支持定时任务自动执行
- 完整的日志记录

## 支持的新闻源

1. **Buffalo University News** - https://www.buffalo.edu/news/news-releases.html
2. **IQM Press Releases** - https://meetiqm.com/company/press-releases/
3. **Science Daily (Quantum Physics)** - https://www.sciencedaily.com/news/matter_energy/quantum_physics/

## 项目结构

```
crawlingNews/
├── README.md                  # 项目说明文档
├── requirements.txt           # Python 依赖包
├── main.py                    # 主程序入口
├── scheduler.py               # 定时任务调度器
├── logger.py                  # 日志配置模块
├── buffalo_crawler.py         # Buffalo University 爬虫
├── iqm_crawler.py            # IQM 爬虫
├── sciencedaily_crawler.py   # Science Daily 爬虫
├── output/                    # 采集结果存放目录
└── logs/                      # 日志文件目录
```

## 环境配置

### 快速开始（推荐）

使用自动配置脚本快速设置环境：

**macOS/Linux:**

```bash
./setup.sh
```

**Windows:**

```bash
setup.bat
```

脚本会自动完成：
- 创建虚拟环境
- 安装所有依赖包
- 创建必要的目录

### 手动配置

#### 1. 创建虚拟环境（推荐）

为了避免污染全局 Python 环境，强烈建议使用虚拟环境：

**macOS/Linux:**

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

**Windows:**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

#### 2. 安装依赖

确保虚拟环境已激活（命令行前面会显示 `(venv)`），然后安装依赖包：

```bash
pip install -r requirements.txt
```

如果需要退出虚拟环境：

```bash
deactivate
```

## 使用方法

### 1. 手动执行采集

采集昨天的新闻（默认行为）：

```bash
python main.py
```

采集指定日期的新闻：

```bash
python main.py --date 2025-12-25
```

只查看结果不保存文件：

```bash
python main.py --no-save
```

指定输出目录：

```bash
python main.py --output /path/to/output
```

### 2. 定时任务执行

启动定时任务（默认每天凌晨2点执行）：

```bash
python scheduler.py
```

自定义执行时间：

```bash
python scheduler.py --time 03:30
```

立即执行一次采集任务：

```bash
python scheduler.py --run-now
```

### 3. 单独测试某个爬虫

测试 Buffalo University 爬虫：

```bash
python buffalo_crawler.py
```

测试 IQM 爬虫：

```bash
python iqm_crawler.py
```

测试 Science Daily 爬虫：

```bash
python sciencedaily_crawler.py
```

## 输出格式

采集结果保存为 JSON 文件，格式示例：

```json
{
  "date": "2025-12-25",
  "crawl_time": "2025-12-26 02:00:15",
  "total_count": 5,
  "news_by_source": {
    "Buffalo University": 2,
    "IQM": 1,
    "Science Daily": 2
  },
  "news": [
    {
      "source": "Buffalo University",
      "title": "新闻标题",
      "date": "2025-12-25",
      "link": "https://...",
      "raw_date": "December 25, 2025"
    }
  ]
}
```

## 日志说明

日志文件保存在 `logs/` 目录下，按日期命名：

- `news_crawler_20251226.log` - 主程序日志
- `scheduler_20251226.log` - 定时任务日志

日志包含：
- 采集开始和结束时间
- 每个爬虫的执行状态
- 采集到的新闻数量
- 错误和异常信息

## 注意事项

1. **网络连接**: 确保网络连接稳定，爬虫需要访问外部网站
2. **网站结构变化**: 如果目标网站更新了页面结构，爬虫可能需要相应调整
3. **访问频率**: 程序已设置合理的请求头，避免频繁请求
4. **日期匹配**: 爬虫会严格匹配指定日期的新闻，如果网站上没有该日期的新闻，结果为空

## 故障排查

### 1. 采集结果为空

- 检查目标网站是否可以正常访问
- 确认目标日期是否有新闻发布
- 查看日志文件了解具体错误信息

### 2. 日期解析失败

- 网站可能使用了不同的日期格式
- 可以修改对应爬虫的 `_parse_date` 方法添加新的日期格式

### 3. 依赖安装失败

**macOS SSL 证书问题:**

如果在 macOS 上遇到 SSL 证书错误（`SSL: CERTIFICATE_VERIFY_FAILED`），有以下解决方案：

**方案 1: 运行 SSL 修复脚本（推荐）**
```bash
./fix_ssl.sh
```

**方案 2: 手动安装 Python SSL 证书**
```bash
# 查找并运行 Python 证书安装脚本
/Applications/Python*/Install\ Certificates.command
```

**方案 3: 使用可信主机安装（临时方案）**
```bash
source venv/bin/activate
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

**其他依赖问题:**

确保使用正确的 pip 版本：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 扩展功能

### 添加新的新闻源

1. 创建新的爬虫文件（参考现有爬虫）
2. 实现 `get_yesterday_news()` 方法
3. 在 [main.py](main.py:20-24) 的 `NewsAggregator.__init__()` 中添加新爬虫

示例：

```python
from your_crawler import YourCrawler

class NewsAggregator:
    def __init__(self, output_dir='output'):
        self.crawlers = [
            BuffaloNewsCrawler(),
            IQMNewsCrawler(),
            ScienceDailyCrawler(),
            YourCrawler()  # 添加新爬虫
        ]
```

## 许可证

MIT License

## 技术支持

如有问题或建议，请查看日志文件或联系开发者。
