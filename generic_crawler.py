"""
Generic Crawler - Configuration-driven web scraper
Reads site configuration from YAML files and extracts news accordingly.
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import yaml
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from request_manager import RequestManager
from exceptions import CrawlerException, RSSFeedError


logger = logging.getLogger(__name__)


class SiteConfig:
    """Site configuration loaded from YAML."""

    def __init__(self, config_path: str):
        """Load configuration from YAML file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        self.name = self._config.get('name', 'Unknown')
        self.enabled = self._config.get('enabled', True)
        self.type = self._config.get('type', 'html')  # rss or html

        self.rss = self._config.get('rss', {})
        self.html = self._config.get('html', {})
        self.content = self._config.get('content', {})

    @property
    def rss_urls(self) -> List[str]:
        return self.rss.get('urls', [])

    @property
    def html_url(self) -> str:
        return self.html.get('url', '')

    @property
    def selectors(self) -> Dict:
        return self.html.get('selectors', {})

    @property
    def date_config(self) -> Dict:
        return self.html.get('date', {})

    @property
    def link_prefix(self) -> str:
        return self.html.get('link_prefix', '')


class GenericCrawler:
    """
    Generic crawler that works with any site configuration.
    Supports both RSS and HTML scraping based on config.
    """

    def __init__(self, config: SiteConfig):
        """
        Initialize crawler with site configuration.

        Args:
            config: SiteConfig object loaded from YAML
        """
        self.config = config
        self.request_manager = RequestManager()
        self.logger = logging.getLogger(f"Crawler:{config.name}")

    def get_news_with_fallback(self, target_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get news with RSS-first strategy and HTML fallback.

        Args:
            target_date: Target date to filter news (default: yesterday)

        Returns:
            List of news dictionaries
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        # Try RSS first if configured
        if self.config.type == 'rss' and self.config.rss_urls:
            try:
                news = self._fetch_rss(target_date)
                if news:
                    self.logger.info(f"Got {len(news)} articles from RSS")
                    return news
                self.logger.info("No RSS results, trying HTML fallback")
            except Exception as e:
                self.logger.warning(f"RSS failed: {e}, trying HTML fallback")

        # Fall back to HTML scraping
        if self.config.html_url:
            try:
                return self._fetch_html(target_date)
            except Exception as e:
                self.logger.error(f"HTML scraping failed: {e}")

        return []

    def _fetch_rss(self, target_date: datetime) -> List[Dict]:
        """Fetch news from RSS feeds."""
        target_date_str = target_date.strftime('%Y-%m-%d')
        all_news = []
        seen_links = set()

        for feed_url in self.config.rss_urls:
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo and not feed.entries:
                    raise RSSFeedError(f"Failed to parse feed: {feed.bozo_exception}")

                for entry in feed.entries:
                    article = self._parse_rss_entry(entry, target_date_str)
                    if article and article['link'] not in seen_links:
                        seen_links.add(article['link'])
                        all_news.append(article)

            except Exception as e:
                self.logger.warning(f"Failed to parse feed {feed_url}: {e}")
                continue

        return all_news

    def _parse_rss_entry(self, entry, target_date_str: str) -> Optional[Dict]:
        """Parse a single RSS entry."""
        title = entry.get('title', '').strip()
        link = entry.get('link', '').strip()

        if not title or not link:
            return None

        # Parse date
        raw_date = self._extract_rss_date(entry)
        parsed_date = self._parse_date(raw_date)

        if not parsed_date or parsed_date.strftime('%Y-%m-%d') != target_date_str:
            return None

        return {
            'source': self.config.name,
            'title': title,
            'date': parsed_date.strftime('%Y-%m-%d'),
            'link': link,
            'raw_date': raw_date,
            'summary': entry.get('summary', '').strip()[:500] if entry.get('summary') else '',
            'feed_source': 'RSS',
        }

    def _extract_rss_date(self, entry) -> str:
        """Extract date string from RSS entry."""
        for field in ['published', 'updated', 'created']:
            if field in entry:
                return entry[field]

        for field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if entry.get(field):
                try:
                    return datetime(*entry[field][:6]).isoformat()
                except (TypeError, ValueError):
                    continue
        return ''

    def _fetch_html(self, target_date: datetime) -> List[Dict]:
        """Fetch news by scraping HTML page."""
        target_date_str = target_date.strftime('%Y-%m-%d')
        self.logger.info(f"[{self.config.name}] 正在采集 {target_date_str} 的新闻...")

        try:
            response = self.request_manager.get(self.config.html_url)
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to fetch {self.config.html_url}: {e}")
            return []

        news = []
        selectors = self.config.selectors
        container_selector = selectors.get('container', '')

        if not container_selector:
            self.logger.warning("No container selector configured")
            return []

        containers = soup.select(container_selector)
        self.logger.info(f"[{self.config.name}] 找到 {len(containers)} 个新闻项")

        for container in containers:
            try:
                article = self._parse_html_container(container, target_date_str)
                if article:
                    news.append(article)
            except Exception as e:
                self.logger.debug(f"Failed to parse container: {e}")
                continue

        self.logger.info(f"[{self.config.name}] 找到 {len(news)} 条 {target_date_str} 的新闻")
        return news

    def _parse_html_container(self, container, target_date_str: str) -> Optional[Dict]:
        """Parse a single HTML container element."""
        selectors = self.config.selectors

        # Extract title
        title_el = container.select_one(selectors.get('title', ''))
        title = title_el.get_text(strip=True) if title_el else ''

        if not title:
            return None

        # Extract link
        link_selector = selectors.get('link', '')
        link = ''
        if link_selector:
            link_el = container.select_one(link_selector)
            if link_el:
                link = link_el.get('href', '')
        elif container.name == 'a' and container.get('href'):
            # Container itself is the link element
            link = container.get('href')

        if link and self.config.link_prefix and not link.startswith('http'):
            link = self.config.link_prefix + link

        if not link:
            return None

        # Extract date
        date_config = self.config.date_config
        raw_date = ''
        parsed_date = None

        date_selector = date_config.get('selector')
        if date_selector:
            date_el = container.select_one(date_selector)
            if date_el:
                # 支持从属性获取日期 (如 datetime 属性)
                date_attr = date_config.get('attribute')
                if date_attr and date_el.get(date_attr):
                    raw_date = date_el.get(date_attr)
                else:
                    raw_date = date_el.get_text(strip=True)
        elif date_config.get('pattern'):
            # Use regex pattern to find date in container text
            text = container.get_text()
            match = re.search(date_config['pattern'], text)
            if match:
                raw_date = match.group()
        else:
            # Try common date selectors
            for sel in ['span.teaser-date', 'span.date', 'time', '.date']:
                date_el = container.select_one(sel)
                if date_el:
                    raw_date = date_el.get_text(strip=True)
                    break

        # Parse date
        if raw_date:
            date_format = date_config.get('format')
            parsed_date = self._parse_date(raw_date, date_format)

        if not parsed_date or parsed_date.strftime('%Y-%m-%d') != target_date_str:
            return None

        # Extract summary if available
        summary = ''
        summary_selector = selectors.get('summary')
        if summary_selector:
            summary_el = container.select_one(summary_selector)
            if summary_el:
                summary = summary_el.get_text(strip=True)[:500]

        return {
            'source': self.config.name,
            'title': title,
            'date': parsed_date.strftime('%Y-%m-%d'),
            'link': link,
            'raw_date': raw_date,
            'summary': summary,
            'feed_source': 'HTML',
        }

    def _parse_date(self, date_str: str, format_str: str = None) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None

        # Try specific format first
        if format_str:
            try:
                return datetime.strptime(date_str.strip(), format_str)
            except ValueError:
                pass

        # Fall back to fuzzy parsing
        try:
            return date_parser.parse(date_str, fuzzy=True)
        except (ValueError, TypeError):
            return None


class SiteRegistry:
    """
    Registry for all configured sites.
    Loads all YAML configs from sites/ directory.
    """

    def __init__(self, sites_dir: str = None):
        """
        Initialize registry and load all site configurations.

        Args:
            sites_dir: Path to sites configuration directory
        """
        if sites_dir is None:
            sites_dir = os.path.join(os.path.dirname(__file__), 'sites')

        self.sites_dir = sites_dir
        self.sites: Dict[str, SiteConfig] = {}
        self.crawlers: Dict[str, GenericCrawler] = {}
        self._load_sites()

    def _load_sites(self):
        """Load all site configurations from YAML files."""
        sites_path = Path(self.sites_dir)
        if not sites_path.exists():
            logger.warning(f"Sites directory not found: {self.sites_dir}")
            return

        for config_file in sites_path.glob('*.yaml'):
            # Skip template files (starting with _)
            if config_file.name.startswith('_'):
                continue

            try:
                config = SiteConfig(str(config_file))
                if config.enabled:
                    self.sites[config.name] = config
                    self.crawlers[config.name] = GenericCrawler(config)
                    logger.info(f"Loaded site config: {config.name}")
            except Exception as e:
                logger.error(f"Failed to load config {config_file}: {e}")

    def get_all_crawlers(self) -> List[GenericCrawler]:
        """Get all enabled crawlers."""
        return list(self.crawlers.values())

    def get_crawler(self, name: str) -> Optional[GenericCrawler]:
        """Get crawler by site name."""
        return self.crawlers.get(name)

    def list_sites(self) -> List[str]:
        """List all enabled site names."""
        return list(self.sites.keys())


# Convenience function
def create_crawlers_from_config(sites_dir: str = None) -> List[GenericCrawler]:
    """
    Create crawlers from all site configurations.

    Args:
        sites_dir: Path to sites configuration directory

    Returns:
        List of GenericCrawler instances
    """
    registry = SiteRegistry(sites_dir)
    return registry.get_all_crawlers()
