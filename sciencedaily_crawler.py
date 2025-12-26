"""
Science Daily Quantum Physics News Crawler
采集 Science Daily 量子物理相关新闻
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import re


class ScienceDailyCrawler:
    def __init__(self):
        # 量子物理分类页面
        self.base_url = "https://www.sciencedaily.com/news/matter_energy/quantum_physics/"
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

        print(f"[Science Daily] 正在采集 {target_date.strftime('%Y-%m-%d')} 的新闻...")

        news_list = []

        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Science Daily 的新闻项结构:
            # <div class="col-md-6">
            #   <div class="latest-head"><a href="/releases/...">标题</a></div>
            #   <div class="latest-summary"><span class="story-date">日期</span> 摘要...</div>
            # </div>

            # 查找所有新闻项容器
            news_containers = soup.find_all('div', class_='col-md-6')

            print(f"[Science Daily] 找到 {len(news_containers)} 个新闻项")

            # 使用 set 去重（同一新闻可能出现多次）
            processed_links = set()

            for container in news_containers:
                try:
                    # 提取标题和链接
                    title_div = container.find('div', class_='latest-head')
                    if not title_div:
                        continue

                    link_elem = title_div.find('a', href=True)
                    if not link_elem:
                        continue

                    title = link_elem.get_text(strip=True)
                    if not title:
                        continue

                    link = link_elem.get('href', '')

                    # 补全链接
                    if link and not link.startswith('http'):
                        if link.startswith('/'):
                            link = f"https://www.sciencedaily.com{link}"
                        else:
                            link = f"https://www.sciencedaily.com/{link}"

                    # 去重：如果已处理过这个链接，跳过
                    if link in processed_links:
                        continue

                    # 提取日期 - 从 <span class="story-date"> 元素
                    summary_div = container.find('div', class_='latest-summary')
                    if not summary_div:
                        continue

                    date_span = summary_div.find('span', class_='story-date')
                    if not date_span:
                        continue

                    date_str = date_span.get_text(strip=True)

                    # 解析日期（格式: "Dec. 6, 2025"）
                    news_date = self._parse_date(date_str)

                    if not news_date:
                        print(f"[Science Daily] 无法解析日期: {date_str}")
                        continue

                    # 检查是否是目标日期的新闻
                    if news_date.date() == target_date.date():
                        processed_links.add(link)

                        news_list.append({
                            'source': 'Science Daily',
                            'title': title,
                            'date': news_date.strftime('%Y-%m-%d'),
                            'link': link,
                            'raw_date': date_str
                        })

                except Exception as e:
                    print(f"[Science Daily] 解析单条新闻时出错: {e}")
                    continue

            print(f"[Science Daily] 找到 {len(news_list)} 条 {target_date.strftime('%Y-%m-%d')} 的新闻")

        except Exception as e:
            print(f"[Science Daily] 采集失败: {e}")

        return news_list

    def _parse_date(self, date_str: str) -> datetime:
        """
        解析日期字符串

        支持多种日期格式
        """
        if not date_str:
            return None

        date_str = date_str.strip()
        # 移除多余的点号（如 "Dec." -> "Dec"）
        date_str = date_str.replace('.', '')

        # 尝试多种日期格式
        formats = [
            '%B %d, %Y',              # December 25, 2025
            '%b %d, %Y',              # Dec 25, 2025
            '%Y-%m-%d',               # 2025-12-25
            '%m/%d/%Y',               # 12/25/2025
            '%d %B %Y',               # 25 December 2025
            '%d %b %Y',               # 25 Dec 2025
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # 尝试提取日期部分
        date_pattern = r'(\w+ \d{1,2}, \d{4})|(\d{1,2}/\d{1,2}/\d{4})|(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, date_str)
        if match:
            extracted_date = match.group(0).replace('.', '')
            for fmt in formats:
                try:
                    return datetime.strptime(extracted_date, fmt)
                except ValueError:
                    continue

        return None


if __name__ == "__main__":
    crawler = ScienceDailyCrawler()
    news = crawler.get_yesterday_news()

    print(f"\n找到 {len(news)} 条新闻:")
    for item in news:
        print(f"- {item['title']}")
        print(f"  日期: {item['date']}")
        print(f"  链接: {item['link']}")
        if item.get('summary'):
            print(f"  摘要: {item['summary']}")
        print()
