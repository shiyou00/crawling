# 新闻采集系统

每天自动检测和采集指定网站前一天发布的新闻。

## 需求

1. 每天检测采集一些网站最新发布的新闻，要前一天的新闻，比如今天是12月26日，只需要采集12月25日发布的新闻
2. 网站列表：
    - https://www.buffalo.edu/news/news-releases.html
    - https://meetiqm.com/company/press-releases/
    - https://www.sciencedaily.com/news/matter_energy/quantum_physics/

## 快速开始

### 1. 环境配置

**macOS/Linux:**
```bash
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### 2. 运行采集

激活虚拟环境后运行：

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# 首先运行测试验证系统
python test.py

# 采集昨天的新闻
python main.py

# 或指定日期
python main.py --date 2025-12-25
```

### 3. 定时任务

启动定时任务（每天凌晨2点自动采集）：

```bash
python scheduler.py
```

立即执行一次测试：

```bash
python scheduler.py --run-now
```

## 项目结构

- `main.py` - 主程序入口
- `test.py` - 系统测试脚本
- `scheduler.py` - 定时任务调度器
- `buffalo_crawler.py` - Buffalo University 爬虫
- `iqm_crawler.py` - IQM 爬虫
- `sciencedaily_crawler.py` - Science Daily 爬虫
- `logger.py` - 日志配置
- `setup.sh` / `setup.bat` - 环境配置脚本
- `fix_ssl.sh` - SSL 证书修复脚本（macOS）
- `output/` - 采集结果存放目录（JSON格式）
- `logs/` - 日志文件目录

## 详细文档

查看 [USAGE.md](USAGE.md) 了解完整使用说明、配置选项和故障排查。

## 系统要求

- Python 3.7+
- 稳定的网络连接