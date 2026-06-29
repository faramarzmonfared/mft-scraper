"""Abstract base class for all MFT Shiraz scrapers."""

import logging
import time
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class providing common HTTP fetching functionality.

    All concrete scrapers must inherit from this class and implement
    the parse method.

    Args:
        base_url: The root URL of the target website.
        delay: Seconds to wait between consecutive requests.
    """

    def __init__(self, base_url: str, delay: float = 1.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )

    def fetch(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return a parsed BeautifulSoup object.

        Args:
            url: The full URL to fetch.

        Returns:
            Parsed BeautifulSoup object of the response HTML.

        Raises:
            requests.HTTPError: If the response status code indicates an error.
            requests.ConnectionError: If the connection fails.
            requests.Timeout: If the request times out.
        """
        max_retries = 3
        for attempt in range(max_retries):
            logger.info("Fetching URL: %s (attempt %d)", url, attempt + 1)
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                time.sleep(self.delay)
                return BeautifulSoup(response.text, "html.parser")
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    wait = self.delay * (2 ** attempt)
                    logger.warning("Rate limited. Waiting %.1fs before retry...", wait)
                    time.sleep(wait)
                    continue
                logger.error("HTTP error for %s: %s", url, e)
                raise
            except requests.ConnectionError as e:
                wait = self.delay * (2 ** attempt)
                logger.warning("Connection error for %s. Waiting %.1fs before retry...", url, wait)
                time.sleep(wait)
                continue
            except requests.Timeout as e:
                logger.error("Timeout for %s: %s", url, e)
                raise

        raise requests.RequestException(f"Failed after {max_retries} retries: {url}")

    @abstractmethod
    def parse(self, soup: BeautifulSoup) -> list:
        """Parse a BeautifulSoup object and return extracted data.

        Args:
            soup: Parsed HTML of the target page.

        Returns:
            List of extracted data objects.
        """

    def run(self, url: str) -> list:
        """Fetch a URL and parse its content.

        Args:
            url: The full URL to scrape.

        Returns:
            List of extracted data objects.
        """
        soup = self.fetch(url)
        return self.parse(soup)
    