"""
Configuration Module
Centralized configuration with environment variable support.
"""

import os


class Config:
    """Application configuration with environment variable overrides."""

    # Request settings
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', 1.0))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    BACKOFF_FACTOR = float(os.getenv('BACKOFF_FACTOR', 2.0))

    # Crawler settings
    RSS_ENABLED = os.getenv('RSS_ENABLED', 'true').lower() == 'true'
    FALLBACK_TO_HTML = os.getenv('FALLBACK_TO_HTML', 'true').lower() == 'true'

    # Rate limiting
    REQUESTS_PER_SECOND = float(os.getenv('REQUESTS_PER_SECOND', 1.0))

    # Proxy settings (for future use)
    PROXY_ENABLED = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
    PROXY_LIST = [p.strip() for p in os.getenv('PROXY_LIST', '').split(',') if p.strip()]

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')

    # Output
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')

    @classmethod
    def as_dict(cls):
        """Return configuration as dictionary."""
        return {
            'request_timeout': cls.REQUEST_TIMEOUT,
            'request_delay': cls.REQUEST_DELAY,
            'max_retries': cls.MAX_RETRIES,
            'backoff_factor': cls.BACKOFF_FACTOR,
            'rss_enabled': cls.RSS_ENABLED,
            'fallback_to_html': cls.FALLBACK_TO_HTML,
            'requests_per_second': cls.REQUESTS_PER_SECOND,
            'proxy_enabled': cls.PROXY_ENABLED,
            'log_level': cls.LOG_LEVEL,
        }
