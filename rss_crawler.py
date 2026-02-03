"""
RSS Crawler Base Class
Abstract RSS feed parser for news sources.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import feedparser
from dateutil import parser as date_parser

from exceptions import RSSFeedError
from config import Config


logger = logging.getLogger(__name__)


class RSSCrawler(ABC):
    """
    Base class for RSS feed crawlers.
    Parses RSS/Atom feeds and converts entries to standard news format.
    """

    def __init__(self, source_name: str, feed_urls: List[str]):
        """
        Initialize RSS crawler.

        Args:
            source_name: Display name for this news source
            feed_urls: List of RSS feed URLs to parse
        """
        self.source_name = source_name
        self.feed_urls = feed_urls
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_yesterday_news(self, target_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get news articles from the target date.

        Args:
            target_date: Date to filter news (default: yesterday)

        Returns:
            List of news dictionaries in standard format
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        target_date_str = target_date.strftime('%Y-%m-%d')
        all_news = []
        seen_links = set()

        for feed_url in self.feed_urls:
            try:
                news = self._parse_feed(feed_url, target_date_str)
                for item in news:
                    if item['link'] not in seen_links:
                        seen_links.add(item['link'])
                        all_news.append(item)
            except RSSFeedError as e:
                self.logger.warning(f"Failed to parse feed {feed_url}: {e}")
                continue

        self.logger.info(f"Found {len(all_news)} articles from {self.source_name} RSS")
        return all_news

    def _parse_feed(self, feed_url: str, target_date_str: str) -> List[Dict]:
        """
        Parse a single RSS feed.

        Args:
            feed_url: URL of the RSS feed
            target_date_str: Target date in YYYY-MM-DD format

        Returns:
            List of news dictionaries
        """
        self.logger.debug(f"Parsing RSS feed: {feed_url}")

        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            raise RSSFeedError(f"Failed to parse feed: {feed.bozo_exception}")

        news = []
        for entry in feed.entries:
            try:
                article = self._parse_entry(entry)
                if article and article.get('date') == target_date_str:
                    news.append(article)
            except Exception as e:
                self.logger.debug(f"Failed to parse entry: {e}")
                continue

        return news

    def _parse_entry(self, entry) -> Optional[Dict]:
        """
        Parse a single feed entry to standard format.

        Args:
            entry: feedparser entry object

        Returns:
            Dictionary with news data or None if parsing fails
        """
        title = entry.get('title', '').strip()
        link = entry.get('link', '').strip()

        if not title or not link:
            return None

        # Parse date from various fields
        raw_date = self._extract_date_string(entry)
        parsed_date = self._parse_date(raw_date)

        if not parsed_date:
            return None

        return {
            'source': self.source_name,
            'title': title,
            'date': parsed_date.strftime('%Y-%m-%d'),
            'link': link,
            'raw_date': raw_date,
            'summary': entry.get('summary', '').strip()[:500] if entry.get('summary') else '',
            'feed_source': 'RSS',
        }

    def _extract_date_string(self, entry) -> str:
        """Extract date string from feed entry."""
        # Try different date fields
        for field in ['published', 'updated', 'created']:
            if field in entry:
                return entry[field]

        # Try parsed time tuple
        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if entry.get(field):
                try:
                    return datetime(*entry[field][:6]).isoformat()
                except (TypeError, ValueError):
                    continue

        return ''

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None

        try:
            return date_parser.parse(date_str, fuzzy=True)
        except (ValueError, TypeError):
            self.logger.debug(f"Failed to parse date: {date_str}")
            return None

    @abstractmethod
    def get_html_fallback_crawler(self):
        """
        Return the HTML crawler instance for fallback.
        Subclasses must implement this to provide fallback capability.
        """
        pass

    def get_news_with_fallback(self, target_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get news with automatic fallback to HTML scraping.

        Args:
            target_date: Date to filter news (default: yesterday)

        Returns:
            List of news dictionaries
        """
        if not Config.RSS_ENABLED:
            self.logger.info("RSS disabled, using HTML crawler")
            return self.get_html_fallback_crawler().get_yesterday_news(target_date)

        try:
            news = self.get_yesterday_news(target_date)
            if news:
                return news

            self.logger.info(f"No RSS results for {self.source_name}, trying HTML fallback")
        except RSSFeedError as e:
            self.logger.warning(f"RSS failed for {self.source_name}: {e}")

        if Config.FALLBACK_TO_HTML:
            try:
                fallback = self.get_html_fallback_crawler()
                return fallback.get_yesterday_news(target_date)
            except Exception as e:
                self.logger.error(f"HTML fallback also failed: {e}")
                return []

        return []
