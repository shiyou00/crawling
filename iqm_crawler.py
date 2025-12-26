"""
IQM Press Releases Crawler
采集 IQM 的新闻发布
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import re


class IQMNewsCrawler:
    def __init__(self):
        self.base_url = "https://meetiqm.com/company/press-releases/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_yesterday_news(self, target_date: datetime = None) -> List[Dict]:
        """
        获取指定日期的新闻（默认为昨天）

        Args:
            target_date: 目标日期，默认为昨天

        Returns:
            新闻列表，每条新闻包含标题、日期、链接等信息
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        print(f"[IQM] 正在采集 {target_date.strftime('%Y-%m-%d')} 的新闻...")

        news_list = []

        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # IQM 使用 div[class*="press"] 包含新闻项
            news_items = soup.select('div[class*="press"]')

            print(f"[IQM] 找到 {len(news_items)} 个新闻项")

            for item in news_items:
                try:
                    # 提取标题 - IQM 的标题在 a 标签中
                    title_elem = item.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # 提取链接
                    link = title_elem.get('href', '')
                    if link and not link.startswith('http'):
                        if link.startswith('/'):
                            link = f"https://meetiqm.com{link}"
                        else:
                            link = f"https://meetiqm.com/{link}"

                    # 提取日期 - IQM 的日期格式是 "DD Mon" 或 "DD Mon YYYY"
                    # 日期在新闻项的文本中
                    full_text = item.get_text()

                    # 使用正则表达式查找日期
                    # 格式: DD Mon 或 DD Mon YYYY
                    date_pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\s+\d{4})?)'
                    date_match = re.search(date_pattern, full_text, re.IGNORECASE)

                    date_str = ''
                    if date_match:
                        date_str = date_match.group(1)

                    # 解析日期
                    news_date = self._parse_date(date_str, target_date.year)

                    # 检查是否是目标日期的新闻
                    if news_date and news_date.date() == target_date.date():
                        news_list.append({
                            'source': 'IQM',
                            'title': title,
                            'date': news_date.strftime('%Y-%m-%d'),
                            'link': link,
                            'raw_date': date_str
                        })

                except Exception as e:
                    print(f"[IQM] 解析单条新闻时出错: {e}")
                    continue

            print(f"[IQM] 找到 {len(news_list)} 条 {target_date.strftime('%Y-%m-%d')} 的新闻")

        except Exception as e:
            print(f"[IQM] 采集失败: {e}")

        return news_list

    def _parse_date(self, date_str: str, default_year: int = None) -> datetime:
        """
        解析日期字符串

        支持多种日期格式，特别是 IQM 的格式:
        - 14 Nov 2025 (DD Mon YYYY)
        - 23 Dec (DD Mon) - 没有年份时使用 default_year
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # 如果没有指定默认年份，使用当前年份
        if default_year is None:
            default_year = datetime.now().year

        # 尝试多种日期格式
        formats = [
            '%d %b %Y',                   # 14 Nov 2025 (IQM 格式)
            '%d %B %Y',                   # 14 November 2025
            '%d %b',                      # 23 Dec (没有年份)
            '%d %B',                      # 23 December (没有年份)
            '%Y-%m-%dT%H:%M:%S',          # ISO 8601 格式
            '%Y-%m-%d',                   # 2025-12-25
            '%B %d, %Y',                  # December 25, 2025
            '%b %d, %Y',                  # Dec 25, 2025
            '%m/%d/%Y',                   # 12/25/2025
            '%d.%m.%Y',                   # 25.12.2025
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # 如果格式没有年份（%d %b 或 %d %B），添加默认年份
                if parsed_date.year == 1900:  # strptime 默认年份
                    parsed_date = parsed_date.replace(year=default_year)
                return parsed_date
            except ValueError:
                continue

        # 尝试提取日期部分
        # 格式: DD Mon YYYY 或 DD Mon
        date_patterns = [
            (r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', '%d %b %Y'),
            (r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))', '%d %b'),
        ]

        for pattern, fmt in date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    parsed_date = datetime.strptime(match.group(1), fmt)
                    if parsed_date.year == 1900:
                        parsed_date = parsed_date.replace(year=default_year)
                    return parsed_date
                except ValueError:
                    continue

        # ISO 8601
        iso_pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(iso_pattern, date_str)
        if match:
            try:
                return datetime.strptime(match.group(0), '%Y-%m-%d')
            except ValueError:
                pass

        return None


if __name__ == "__main__":
    crawler = IQMNewsCrawler()
    news = crawler.get_yesterday_news()

    print(f"\n找到 {len(news)} 条新闻:")
    for item in news:
        print(f"- {item['title']}")
        print(f"  日期: {item['date']}")
        print(f"  链接: {item['link']}\n")
