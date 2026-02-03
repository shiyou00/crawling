"""
Science Daily RSS Crawler
RSS feed parser for Science Daily quantum physics news.
"""

import logging
from rss_crawler import RSSCrawler
from sciencedaily_crawler import ScienceDailyCrawler


logger = logging.getLogger(__name__)


class ScienceDailyRSSCrawler(RSSCrawler):
    """
    RSS crawler for Science Daily quantum physics news.
    Uses RSS as primary source with HTML fallback.
    """

    # Science Daily RSS feeds for quantum physics
    FEED_URLS = [
        'https://www.sciencedaily.com/rss/matter_energy/quantum_physics.xml',
    ]

    def __init__(self):
        super().__init__(
            source_name='Science Daily',
            feed_urls=self.FEED_URLS
        )
        self._html_crawler = None

    def get_html_fallback_crawler(self):
        """Return HTML crawler for fallback."""
        if self._html_crawler is None:
            self._html_crawler = ScienceDailyCrawler()
        return self._html_crawler


if __name__ == '__main__':
    # Test the crawler
    logging.basicConfig(level=logging.DEBUG)
    crawler = ScienceDailyRSSCrawler()
    news = crawler.get_news_with_fallback()
    print(f"Found {len(news)} articles")
    for item in news[:3]:
        print(f"  - {item['title'][:60]}...")
