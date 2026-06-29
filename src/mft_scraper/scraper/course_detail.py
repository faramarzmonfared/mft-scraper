"""Scraper for extracting detailed description from a course page."""

import logging
import re

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

    def parse(self, soup: BeautifulSoup) -> list[CourseDetail]:
        """Parse course detail from a course page.

        Args:
            soup: Parsed HTML of the course detail page.

        Returns:
            List containing a single CourseDetail object, or empty list on failure.
        """
        # Extract course_id from canonical link or register button
        course_id: int = 0
        register_anchor = soup.find("a", href=re.compile(r"/studentPanel/register/(\d+)"))
        if register_anchor:
            match = re.search(r"/register/(\d+)", str(register_anchor["href"]))
            if match:
                course_id = int(match.group(1))

        if not course_id:
            logger.warning("Could not extract course_id from page")
            return []

        # Extract description block after <hr>
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
    