"""
Buffalo University RSS Crawler
RSS feed parser for Buffalo University news.
Note: Buffalo University may not have an RSS feed, so this primarily uses HTML fallback.
"""

import logging
from rss_crawler import RSSCrawler
from buffalo_crawler import BuffaloNewsCrawler


logger = logging.getLogger(__name__)


class BuffaloRSSCrawler(RSSCrawler):
    """
    RSS crawler for Buffalo University news.
    Note: Buffalo may not provide RSS, so HTML fallback is the primary method.
    """

    # Buffalo University RSS feeds (to be verified)
    # These URLs are speculative - actual RSS availability needs verification
    FEED_URLS = [
        'https://www.buffalo.edu/news/news-releases.xml',
        'https://www.buffalo.edu/news/rss.xml',
    ]

    def __init__(self):
        super().__init__(
            source_name='Buffalo University',
            feed_urls=self.FEED_URLS
        )
        self._html_crawler = None

    def get_html_fallback_crawler(self):
        """Return HTML crawler for fallback."""
        if self._html_crawler is None:
            self._html_crawler = BuffaloNewsCrawler()
        return self._html_crawler


if __name__ == '__main__':
    # Test the crawler
    logging.basicConfig(level=logging.DEBUG)
    crawler = BuffaloRSSCrawler()
    news = crawler.get_news_with_fallback()
    print(f"Found {len(news)} articles")
    for item in news[:3]:
        print(f"  - {item['title'][:60]}...")
