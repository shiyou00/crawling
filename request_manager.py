"""
Request Manager Module
Centralized HTTP request handling with anti-crawling protections.
"""

import time
import logging
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

import cloudscraper
from http_config import UserAgents, HTTPDefaults
from config import Config
from exceptions import RequestError


logger = logging.getLogger(__name__)


class RequestManager:
    """
    Manages HTTP requests with anti-crawling features:
    - User-Agent rotation
    - Request rate limiting
    - Exponential backoff retry
    - Configurable timeouts
    """

    def __init__(
        self,
        timeout=None,
        delay=None,
        max_retries=None,
        backoff_factor=None,
        rotate_ua=True
    ):
        """
        Initialize RequestManager.

        Args:
            timeout: Request timeout in seconds
            delay: Minimum delay between requests in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
            rotate_ua: Whether to rotate User-Agent per request
        """
        self.timeout = timeout or Config.REQUEST_TIMEOUT
        self.delay = delay or Config.REQUEST_DELAY
        self.max_retries = max_retries or Config.MAX_RETRIES
        self.backoff_factor = backoff_factor or Config.BACKOFF_FACTOR
        self.rotate_ua = rotate_ua

        self._last_request_time = 0
        self._session = requests.Session()
        self._cloudscraper_session = None

    def _get_headers(self):
        """Get request headers with optional UA rotation."""
        if self.rotate_ua:
            return HTTPDefaults.get_headers(UserAgents.get_random())
        return HTTPDefaults.get_headers()

    def _wait_for_rate_limit(self):
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

    def _should_retry(self, response=None, exception=None):
        """Determine if request should be retried."""
        if exception:
            return isinstance(exception, (Timeout, ConnectionError))
        if response:
            return response.status_code in HTTPDefaults.RETRY_STATUS_CODES
        return False

    def _get_cloudscraper_session(self):
        """Get or create a cloudscraper session for Cloudflare bypass."""
        if self._cloudscraper_session is None:
            try:
                scraper = cloudscraper.create_scraper()
                self._cloudscraper_session = scraper
                logger.info("cloudscraper session created for Cloudflare bypass")
            except Exception as e:
                logger.warning(f"Failed to create cloudscraper session: {e}")
        return self._cloudscraper_session

    def _try_cloudscraper(self, url):
        """Try cloudscraper as Cloudflare bypass, return response or None."""
        cs_session = self._get_cloudscraper_session()
        if not cs_session:
            return None
        logger.info(f"Standard request blocked, trying cloudscraper: {url}")
        try:
            cs_response = cs_session.get(url, timeout=self.timeout)
            if cs_response.status_code == 200:
                self._last_request_time = time.time()
                return cs_response
            logger.warning(f"cloudscraper also failed with status {cs_response.status_code}")
        except Exception as e:
            logger.warning(f"cloudscraper request failed: {e}")
        return None

    def _try_playwright(self, url):
        """Try Playwright headless browser as final Cloudflare bypass."""
        try:
            from playwright.sync_api import sync_playwright
            from playwright_stealth import Stealth
            logger.info(f"cloudscraper failed, trying Playwright headless browser: {url}")
            stealth = Stealth()
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context()
                stealth.apply_stealth_sync(context)
                page = context.new_page()
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                # Wait for Cloudflare challenge to resolve
                page.wait_for_function(
                    "document.title !== 'Just a moment...'",
                    timeout=30000
                )
                content = page.content()
                browser.close()
                class PlaywrightResponse:
                    def __init__(self, text, status_code=200):
                        self.text = text
                        self.status_code = status_code
                        self.content = text.encode('utf-8')
                self._last_request_time = time.time()
                return PlaywrightResponse(content)
        except Exception as e:
            logger.warning(f"Playwright bypass failed: {e}")
        return None

    def get(self, url, **kwargs):
        """
        Make a GET request with retry logic and rate limiting.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments passed to requests.get()

        Returns:
            requests.Response object

        Raises:
            RequestError: If all retries fail
        """
        last_exception = None
        last_response = None

        for attempt in range(self.max_retries + 1):
            try:
                self._wait_for_rate_limit()

                headers = kwargs.pop('headers', None) or self._get_headers()
                timeout = kwargs.pop('timeout', None) or self.timeout

                logger.debug(f"Request attempt {attempt + 1}/{self.max_retries + 1}: {url}")

                response = self._session.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    **kwargs
                )

                self._last_request_time = time.time()

                if response.status_code == 200:
                    return response

                # Cloudflare bypass: try cloudscraper then playwright on 403/503
                if response.status_code in (403, 503):
                    last_response = response
                    cs_response = self._try_cloudscraper(url)
                    if cs_response:
                        return cs_response
                    pw_response = self._try_playwright(url)
                    if pw_response:
                        return pw_response

                if self._should_retry(response=response):
                    last_response = response
                    wait_time = self.delay * (self.backoff_factor ** attempt)
                    logger.warning(
                        f"Request failed with status {response.status_code}, "
                        f"retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    continue

                # Non-retryable error
                response.raise_for_status()

            except (Timeout, ConnectionError) as e:
                last_exception = e
                self._last_request_time = time.time()

                if attempt < self.max_retries:
                    wait_time = self.delay * (self.backoff_factor ** attempt)
                    logger.warning(
                        f"Request error: {e}, retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                continue

            except RequestException as e:
                logger.error(f"Request failed: {e}")
                raise RequestError(f"Request to {url} failed: {e}") from e

        # All retries exhausted
        if last_exception:
            raise RequestError(
                f"Request to {url} failed after {self.max_retries + 1} attempts: {last_exception}"
            ) from last_exception

        if last_response:
            raise RequestError(
                f"Request to {url} failed with status {last_response.status_code} "
                f"after {self.max_retries + 1} attempts"
            )

        raise RequestError(f"Request to {url} failed for unknown reason")

    def close(self):
        """Close the underlying sessions."""
        self._session.close()
        if self._cloudscraper_session:
            self._cloudscraper_session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global instance for convenience
_default_manager = None


def get_request_manager():
    """Get or create the default RequestManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = RequestManager()
    return _default_manager


def fetch_url(url, **kwargs):
    """Convenience function to fetch a URL using the default manager."""
    return get_request_manager().get(url, **kwargs)
