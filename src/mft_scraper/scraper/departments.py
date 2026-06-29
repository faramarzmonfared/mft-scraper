"""Scraper for extracting department list from MFT Shiraz main page."""

import logging
import re

from bs4 import BeautifulSoup

from .base import BaseScraper
from .schemas import Department

logger = logging.getLogger(__name__)


class DepartmentScraper(BaseScraper):
    """Scrapes the list of departments from the main public page.

    Args:
        base_url: The root URL of the target website.
        delay: Seconds to wait between consecutive requests.
    """

    def parse(self, soup: BeautifulSoup) -> list[Department]:
        """Parse department cards from the main page.

        Args:
            soup: Parsed HTML of the main public page.

        Returns:
            List of Department objects.
        """
        departments: list[Department] = []

        cards = soup.select("div.col-md-3")
        logger.info("Found %d candidate cards", len(cards))

        for card in cards:
            anchor = card.find("a", href=True)
            name_tag = card.find("p")

            if not anchor or not name_tag:
                continue

            href: str = str(anchor["href"])
            match = re.search(r"/department/(\d+)", href)
            if not match:
                continue

            dept_id = int(match.group(1))
            name = name_tag.get_text(strip=True)
            url = href if href.startswith("http") else self.base_url + href

            departments.append(
                Department(id=dept_id, name=name, url=url)
            )
            logger.debug("Parsed department: id=%d name=%s", dept_id, name)

        logger.info("Total departments parsed: %d", len(departments))
        return departments