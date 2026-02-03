"""
IQM RSS Crawler
RSS feed parser for IQM press releases.
Note: IQM may not have an RSS feed, so this primarily uses HTML fallback.
"""

import logging
from rss_crawler import RSSCrawler
from iqm_crawler import IQMNewsCrawler


logger = logging.getLogger(__name__)


class IQMRSSCrawler(RSSCrawler):
    """
    RSS crawler for IQM press releases.
    Note: IQM may not provide RSS, so HTML fallback is the primary method.
    """

    # IQM RSS feeds (to be verified)
    # These URLs are speculative - actual RSS availability needs verification
    FEED_URLS = [
        'https://meetiqm.com/feed/',
        'https://meetiqm.com/company/press-releases/feed/',
    ]

    def __init__(self):
        super().__init__(
            source_name='IQM',
            feed_urls=self.FEED_URLS
        )
        self._html_crawler = None

    def get_html_fallback_crawler(self):
        """Return HTML crawler for fallback."""
        if self._html_crawler is None:
            self._html_crawler = IQMNewsCrawler()
        return self._html_crawler


if __name__ == '__main__':
    # Test the crawler
    logging.basicConfig(level=logging.DEBUG)
    crawler = IQMRSSCrawler()
    news = crawler.get_news_with_fallback()
    print(f"Found {len(news)} articles")
    for item in news[:3]:
        print(f"  - {item['title'][:60]}...")
