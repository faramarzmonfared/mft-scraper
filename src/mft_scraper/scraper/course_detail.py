"""Scraper for extracting detailed description from a course page."""

import logging

from bs4 import BeautifulSoup

from .base import BaseScraper
from .schemas import CourseDetail

logger = logging.getLogger(__name__)


class CourseDetailScraper(BaseScraper):
    """Scrapes the description block from an individual course page.

    Args:
        base_url: The root URL of the target website.
        delay: Seconds to wait between consecutive requests.
    """

    def parse(self, soup: BeautifulSoup, course_id: int = 0) -> list[CourseDetail]:
        """Parse course detail from a course page.

        Args:
            soup: Parsed HTML of the course detail page.
            course_id: Course ID passed from the caller (extracted from URL).

        Returns:
            List containing a single CourseDetail object, or empty list on failure.
        """
        hr_tag = soup.find("hr")
        if not hr_tag:
            logger.warning("No <hr> found on course page for id=%d", course_id)
            return []

        desc_div = hr_tag.find_next("div", class_="col-md-12")
        if not desc_div:
            logger.warning("No description div found for course id=%d", course_id)
            return []

        description = desc_div.get_text(separator="\n", strip=True)
        logger.debug("Parsed course detail: id=%d desc_length=%d", course_id, len(description))

        return [CourseDetail(course_id=course_id, description=description)]

    def scrape(self, url: str, course_id: int) -> list[CourseDetail]:
        """Fetch a course page and parse its detail.

        Args:
            url: Full URL of the course detail page.
            course_id: Course ID extracted from the URL by the caller.

        Returns:
            List containing a single CourseDetail object, or empty list on failure.
        """
        soup = self.fetch(url)
        return self.parse(soup, course_id)
    