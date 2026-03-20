#!/usr/bin/env python3
"""
新闻采集主程序
每天采集指定网站的前一天新闻
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
import argparse
import logging

from buffalo_crawler import BuffaloNewsCrawler
from iqm_crawler import IQMNewsCrawler
from sciencedaily_crawler import ScienceDailyCrawler
from buffalo_rss_crawler import BuffaloRSSCrawler
from iqm_rss_crawler import IQMRSSCrawler
from sciencedaily_rss_crawler import ScienceDailyRSSCrawler
from generic_crawler import SiteRegistry, create_crawlers_from_config
from translator import NewsTranslator
from summarizer import ContentSummarizer
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/news_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class NewsAggregator:
    """新闻聚合器，整合所有爬虫"""

    def __init__(self, output_dir='output', enable_translation=True, enable_summary=True, use_rss=None, use_config=False):
        self.output_dir = output_dir
        self.enable_translation = enable_translation
        self.enable_summary = enable_summary

        # 选择爬虫模式
        if use_config:
            # 配置驱动模式：从 sites/ 目录加载 YAML 配置
            logger.info("使用配置驱动模式（从 sites/*.yaml 加载）")
            self.crawlers = create_crawlers_from_config()
            if not self.crawlers:
                logger.warning("未找到有效配置，回退到传统爬虫")
                use_config = False

        if not use_config:
            # 传统模式：使用硬编码的爬虫
            use_rss = use_rss if use_rss is not None else Config.RSS_ENABLED

            if use_rss:
                logger.info("使用 RSS 爬虫（带 HTML 回退）")
                self.crawlers = [
                    BuffaloRSSCrawler(),
                    IQMRSSCrawler(),
                    ScienceDailyRSSCrawler()
                ]
            else:
                logger.info("使用 HTML 爬虫")
                self.crawlers = [
                    BuffaloNewsCrawler(),
                    IQMNewsCrawler(),
                    ScienceDailyCrawler()
                ]

        # 初始化翻译器和摘要器
        if self.enable_translation:
            try:
                self.translator = NewsTranslator()
                logger.info("翻译功能已启用")
            except Exception as e:
                logger.warning(f"翻译器初始化失败: {e}，翻译功能将被禁用")
                self.enable_translation = False

        if self.enable_summary:
            try:
                self.summarizer = ContentSummarizer()
                logger.info("摘要功能已启用")
            except Exception as e:
                logger.warning(f"摘要器初始化失败: {e}，摘要功能将被禁用")
                self.enable_summary = False

        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 创建日志目录
        if not os.path.exists('logs'):
            os.makedirs('logs')

    def crawl_yesterday_news(self, target_date: datetime = None) -> Dict:
        """
        采集昨天的新闻

        Args:
            target_date: 目标日期，默认为昨天

        Returns:
            包含所有新闻的字典
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        print("=" * 60)
        print(f"开始采集 {target_date.strftime('%Y-%m-%d')} 的新闻")
        print("=" * 60)

        all_news = []

        # 依次运行所有爬虫
        for crawler in self.crawlers:
            try:
                # RSS 爬虫使用 get_news_with_fallback，HTML 爬虫使用 get_yesterday_news
                if hasattr(crawler, 'get_news_with_fallback'):
                    news = crawler.get_news_with_fallback(target_date)
                else:
                    news = crawler.get_yesterday_news(target_date)
                all_news.extend(news)
            except Exception as e:
                logger.error(f"爬虫 {crawler.__class__.__name__} 执行失败: {e}")
                print(f"爬虫 {crawler.__class__.__name__} 执行失败: {e}")

        print(f"\n采集到 {len(all_news)} 条新闻")

        # 处理新闻内容（获取摘要）
        if self.enable_summary and all_news:
            print("\n正在获取新闻全文和生成摘要...")
            all_news = self.summarizer.process_news_list(all_news)

        # 翻译新闻
        if self.enable_translation and all_news:
            print("\n正在翻译新闻...")
            all_news = self.translator.translate_news_list(all_news)

        # 整理结果
        result = {
            'date': target_date.strftime('%Y-%m-%d'),
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(all_news),
            'news_by_source': self._group_by_source(all_news),
            'news': all_news,
            'features': {
                'translation_enabled': self.enable_translation,
                'summary_enabled': self.enable_summary
            }
        }

        return result

    def _group_by_source(self, news_list: List[Dict]) -> Dict:
        """按来源分组统计"""
        grouped = {}
        for news in news_list:
            source = news.get('source', 'Unknown')
            if source not in grouped:
                grouped[source] = 0
            grouped[source] += 1
        return grouped

    def save_to_json(self, data: Dict, filename: str = None):
        """保存结果到 JSON 文件"""
        if filename is None:
            date_str = data['date'].replace('-', '')
            filename = f"news_{date_str}.json"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {filepath}")
        return filepath

    def save_to_html(self, data: Dict, filename: str = None):
        """保存结果到 HTML 文件"""
        if filename is None:
            date_str = data['date'].replace('-', '')
            filename = f"news_{date_str}.html"

        filepath = os.path.join(self.output_dir, filename)

        html_content = self._generate_html(data)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML 结果已保存到: {filepath}")
        return filepath

    def _generate_html(self, data: Dict) -> str:
        """生成 HTML 内容"""
        news_cards = ""
        for news in data['news']:
            title_en = news['title']
            title_zh = news.get('title_zh', '')
            summary_en = news.get('summary', '')
            summary_zh = news.get('summary_zh', '')

            # 中文标题部分
            title_zh_html = f'<p class="title-zh">{title_zh}</p>' if title_zh else ""

            # 摘要部分：同时显示中英文
            summary_html = ""
            if summary_zh:
                summary_html += f'<div class="summary-block"><span class="lang-tag">中文</span><p class="news-summary">{summary_zh}</p></div>'
            if summary_en:
                summary_html += f'<div class="summary-block"><span class="lang-tag en">English</span><p class="news-summary original">{summary_en}</p></div>'
            if not summary_html:
                summary_html = '<p class="news-summary">暂无摘要</p>'

            news_cards += f'''
            <div class="news-card">
                <span class="source-tag">{news['source']}</span>
                <h2 class="news-title">
                    <a href="{news['link']}" target="_blank">{title_en}</a>
                </h2>
                {title_zh_html}
                <p class="news-date">📅 {news['date']}</p>
                {summary_html}
            </div>
            '''

        source_stats = ""
        for source, count in data['news_by_source'].items():
            source_stats += f'<span class="stat-item">{source}: {count} 条</span>'

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新闻采集 - {data['date']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 15px;
        }}
        .meta-info {{
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        .stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .stat-item {{
            background: #f0f0f0;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            color: #555;
        }}
        .news-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .news-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }}
        .source-tag {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 12px;
        }}
        .news-title {{
            font-size: 18px;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .news-title a {{
            color: #333;
            text-decoration: none;
        }}
        .news-title a:hover {{
            color: #667eea;
        }}
        .title-zh {{
            font-size: 16px;
            color: #e74c3c;
            margin-bottom: 10px;
            font-weight: 500;
            padding-left: 10px;
            border-left: 3px solid #e74c3c;
        }}
        .news-date {{
            font-size: 13px;
            color: #999;
            margin-bottom: 12px;
        }}
        .summary-block {{
            margin-bottom: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .lang-tag {{
            display: inline-block;
            background: #e74c3c;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            margin-bottom: 8px;
        }}
        .lang-tag.en {{
            background: #3498db;
        }}
        .news-summary {{
            font-size: 15px;
            color: #555;
            line-height: 1.6;
            margin: 0;
        }}
        .news-summary.original {{
            color: #777;
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 14px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 新闻采集报告</h1>
            <div class="meta-info">
                <p>📅 日期: {data['date']} | ⏰ 采集时间: {data['crawl_time']} | 📊 共 {data['total_count']} 条新闻</p>
            </div>
            <div class="stats">
                {source_stats}
            </div>
        </div>

        {news_cards}

        <div class="footer">
            Powered by News Crawler
        </div>
    </div>
</body>
</html>'''
        return html

    def print_summary(self, data: Dict):
        """打印采集摘要"""
        print("\n" + "=" * 60)
        print("采集摘要")
        print("=" * 60)
        print(f"日期: {data['date']}")
        print(f"采集时间: {data['crawl_time']}")
        print(f"总计: {data['total_count']} 条新闻\n")

        # 显示启用的功能
        features = data.get('features', {})
        if features:
            print("启用的功能:")
            if features.get('translation_enabled'):
                print("  ✓ 翻译功能（英文→中文）")
            if features.get('summary_enabled'):
                print("  ✓ 内容摘要")
            print()

        print("各来源统计:")
        for source, count in data['news_by_source'].items():
            print(f"  - {source}: {count} 条")

        print("\n新闻列表:")
        for i, news in enumerate(data['news'], 1):
            print(f"\n{i}. [{news['source']}] {news['title']}")

            # 显示中文标题（如果有）
            if news.get('title_zh'):
                print(f"   【中文】{news['title_zh']}")

            print(f"   日期: {news['date']}")
            print(f"   链接: {news['link']}")

            # 显示摘要
            if news.get('summary'):
                print(f"   摘要: {news['summary'][:150]}...")

            # 显示中文摘要（如果有）
            if news.get('summary_zh'):
                print(f"   【中文摘要】{news['summary_zh'][:150]}...")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description='新闻采集工具')
    parser.add_argument(
        '--date',
        type=str,
        help='指定采集日期 (格式: YYYY-MM-DD)，默认为昨天'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='输出目录，默认为 output'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='不保存到文件，仅打印结果'
    )
    parser.add_argument(
        '--no-translate',
        action='store_true',
        help='禁用翻译功能'
    )
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='禁用内容摘要功能'
    )
    parser.add_argument(
        '--no-rss',
        action='store_true',
        help='禁用 RSS 采集，仅使用 HTML 爬虫'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='使用配置驱动模式（从 sites/*.yaml 加载站点配置）'
    )

    args = parser.parse_args()

    # 解析目标日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"错误: 日期格式不正确，请使用 YYYY-MM-DD 格式")
            return
    else:
        target_date = datetime.now() - timedelta(days=1)

    # 创建聚合器并执行采集
    aggregator = NewsAggregator(
        output_dir=args.output,
        enable_translation=not args.no_translate,
        enable_summary=not args.no_summary,
        use_rss=not args.no_rss,
        use_config=args.config
    )
    result = aggregator.crawl_yesterday_news(target_date)

    # 打印摘要
    aggregator.print_summary(result)

    # 保存结果
    if not args.no_save:
        aggregator.save_to_json(result)
        aggregator.save_to_html(result)


if __name__ == "__main__":
    main()
