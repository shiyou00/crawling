"""
Custom Exceptions for the News Crawler
"""


class CrawlerException(Exception):
    """Base exception for all crawler operations."""
    pass


class RSSFeedError(CrawlerException):
    """RSS feed parsing or fetching failed."""
    pass


class RequestError(CrawlerException):
    """HTTP request failed after all retries."""
    pass


class DateParseError(CrawlerException):
    """Date parsing failed."""
    pass


class ContentExtractionError(CrawlerException):
    """Could not extract content from page."""
    pass
