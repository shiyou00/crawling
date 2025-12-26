"""
Buffalo University News Crawler
采集 Buffalo University 的新闻发布
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import re


class BuffaloNewsCrawler:
    def __init__(self):
        self.base_url = "https://www.buffalo.edu/news/news-releases.html"
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

        print(f"[Buffalo] 正在采集 {target_date.strftime('%Y-%m-%d')} 的新闻...")

        news_list = []

        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Buffalo 使用 ul.list-style-teaser-news 包含所有新闻
            news_list_elem = soup.find('ul', class_='list-style-teaser-news')

            if not news_list_elem:
                print("[Buffalo] 未找到新闻列表容器")
                return news_list

            news_items = news_list_elem.find_all('li')

            print(f"[Buffalo] 找到 {len(news_items)} 个新闻项")

            for item in news_items:
                try:
                    # 提取标题 - Buffalo 使用 div.teaser-title > span
                    title_elem = item.find('div', class_='teaser-title')
                    if not title_elem:
                        continue

                    # 标题文本在 span 中
                    title_span = title_elem.find('span')
                    title = title_span.get_text(strip=True) if title_span else title_elem.get_text(strip=True)

                    # 提取链接 - Buffalo 使用 a.teaser-primary-anchor
                    link_elem = item.find('a', class_='teaser-primary-anchor')
                    link = link_elem.get('href', '') if link_elem else ''
                    if link:
                        # Buffalo 的链接格式是 //www.buffalo.edu/...
                        if link.startswith('//'):
                            link = f"https:{link}"
                        elif not link.startswith('http'):
                            link = f"https://www.buffalo.edu{link}"

                    # 提取日期 - Buffalo 使用 span.teaser-date
                    date_elem = item.find('span', class_='teaser-date')
                    date_str = date_elem.get_text(strip=True) if date_elem else ''

                    # 解析日期
                    news_date = self._parse_date(date_str)

                    # 检查是否是目标日期的新闻
                    if news_date and news_date.date() == target_date.date():
                        news_list.append({
                            'source': 'Buffalo University',
                            'title': title,
                            'date': news_date.strftime('%Y-%m-%d'),
                            'link': link,
                            'raw_date': date_str
                        })

                except Exception as e:
                    print(f"[Buffalo] 解析单条新闻时出错: {e}")
                    continue

            print(f"[Buffalo] 找到 {len(news_list)} 条 {target_date.strftime('%Y-%m-%d')} 的新闻")

        except Exception as e:
            print(f"[Buffalo] 采集失败: {e}")

        return news_list

    def _parse_date(self, date_str: str) -> datetime:
        """
        解析日期字符串

        支持多种日期格式：
        - 12/22/25 (MM/DD/YY) - Buffalo 格式
        - December 25, 2025
        - Dec 25, 2025
        - 12/25/2025
        - 2025-12-25
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # 尝试多种日期格式
        formats = [
            '%m/%d/%y',       # 12/22/25 (Buffalo 格式，两位年份)
            '%m/%d/%Y',       # 12/25/2025
            '%B %d, %Y',      # December 25, 2025
            '%b %d, %Y',      # Dec 25, 2025
            '%Y-%m-%d',       # 2025-12-25
            '%d %B %Y',       # 25 December 2025
            '%d %b %Y',       # 25 Dec 2025
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # 如果年份只有两位数，确保在 2000-2099 范围内
                if parsed_date.year < 100:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                return parsed_date
            except ValueError:
                continue

        # 尝试提取日期部分
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2})',  # MM/DD/YY
            r'(\w+ \d{1,2}, \d{4})',      # Month DD, YYYY
            r'(\d{1,2}/\d{1,2}/\d{4})',   # MM/DD/YYYY
            r'(\d{4}-\d{2}-\d{2})'        # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                extracted_date = match.group(1)
                for fmt in formats:
                    try:
                        parsed_date = datetime.strptime(extracted_date, fmt)
                        if parsed_date.year < 100:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                        return parsed_date
                    except ValueError:
                        continue

        return None


if __name__ == "__main__":
    crawler = BuffaloNewsCrawler()
    news = crawler.get_yesterday_news()

    print(f"\n找到 {len(news)} 条新闻:")
    for item in news:
        print(f"- {item['title']}")
        print(f"  日期: {item['date']}")
        print(f"  链接: {item['link']}\n")
