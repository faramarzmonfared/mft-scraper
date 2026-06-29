"""Scraper for extracting course list from a department page."""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

from .base import BaseScraper
from .schemas import Course, CourseStatus

logger = logging.getLogger(__name__)

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def _to_int(text: str) -> Optional[int]:
    """Convert a Persian/Arabic price string to an integer.

    Args:
        text: Raw price text e.g. '۷۵,۰۰۰,۰۰۰ ریال'.

    Returns:
        Integer value or None if conversion fails.
    """
    try:
        cleaned = text.translate(PERSIAN_DIGITS).replace(",", "").replace("ریال", "").strip()
        return int(cleaned)
    except (ValueError, AttributeError):
        return None


def _parse_status(card: Tag) -> CourseStatus:
    """Extract enrollment status from a course card.

    Args:
        card: BeautifulSoup Tag of the course list item.

    Returns:
        CourseStatus enum value.
    """
    badge = card.find("span", class_="badge")
    if not badge:
        return CourseStatus.ENROLLING
    text = badge.get_text(strip=True)
    if "تکمیل ظرفیت" in text and "درحال" not in text:
        return CourseStatus.FULL
    if "درحال تکمیل" in text:
        return CourseStatus.FILLING
    return CourseStatus.ENROLLING


class CourseScraper(BaseScraper):
    """Scrapes the list of courses from a department page.

    Args:
        base_url: The root URL of the target website.
        delay: Seconds to wait between consecutive requests.
    """

    def parse(self, soup: BeautifulSoup) -> list[Course]:
        """Parse course cards from a department page.

        Args:
            soup: Parsed HTML of the department page.

        Returns:
            List of Course objects.
        """
        courses: list[Course] = []

        # Extract department_id from the active button in search bar
        active_btn = soup.select_one("a.btn.btn-primary[href*='/department/']")
        department_id: int = 0
        if active_btn:
            match = re.search(r"/department/(\d+)", str(active_btn["href"]))
            if match:
                department_id = int(match.group(1))

        cards = soup.select("div.list-group-item[aria-current='true']")
        logger.info("Found %d course cards in department %d", len(cards), department_id)

        for card in cards:
            try:
                course = self._parse_card(card, department_id)
                if course:
                    courses.append(course)
            except Exception as e:
                logger.warning("Failed to parse a course card: %s", e)

        logger.info("Total courses parsed: %d", len(courses))
        return courses

    def _parse_card(self, card: Tag, department_id: int) -> Optional[Course]:
        """Parse a single course card.

        Args:
            card: BeautifulSoup Tag of the course list item.
            department_id: ID of the parent department.

        Returns:
            Course object or None if parsing fails.
        """
        # Name
        name_tag = card.select_one("h4.mb-1")
        if not name_tag:
            return None
        name = name_tag.get_text(strip=True)

        # URL and ID
        detail_anchor = card.find("a", href=re.compile(r"/public/class/\d+"))
        if not detail_anchor:
            return None
        href = str(detail_anchor["href"])
        match = re.search(r"/class/(\d+)", href)
        if not match:
            return None
        course_id = int(match.group(1))
        url = href if href.startswith("http") else self.base_url + href

        # Instructor
        instructor_tag = card.find("span", class_="fa-user")
        instructor = instructor_tag.parent.get_text(strip=True) if instructor_tag and instructor_tag.parent else ""
        # Schedule
        schedule_tags = card.find_all("p", class_="mb-1")
        schedule = ""
        for p in schedule_tags:
            if p.find("span", class_="fa-calendar"):
                schedule = p.get_text(strip=True)
                break

        # Start date
        start_date: Optional[str] = None
        start_note: Optional[str] = None
        for p in schedule_tags:
            text = p.get_text(strip=True)
            if "شروع دوره" in text:
                start_date = text.replace("شروع دوره از:", "").strip()
                break

        if not start_date and "به محض تکمیل ظرفیت" in name:
            start_note = "شروع دوره به محض تکمیل ظرفیت"

        # Duration
        duration_hours: int = 0
        clock_span = card.find("span", class_="fa-clock-o")
        if clock_span:
            duration_text = clock_span.parent.get_text(strip=True).translate(PERSIAN_DIGITS) if clock_span.parent else ""
            dur_match = re.search(r"(\d+)", duration_text)
            if dur_match:
                duration_hours = int(dur_match.group(1))

        # Capacity
        capacity_remaining: int = 0
        users_span = card.find("span", class_="fa-users")
        if users_span:
            cap_text = users_span.parent.get_text(strip=True).translate(PERSIAN_DIGITS) if users_span.parent else ""
            cap_match = re.search(r"(\d+)", cap_text)
            if cap_match:
                capacity_remaining = int(cap_match.group(1))

        # Prices
        original_price: Optional[int] = None
        del_tag = card.find("del")
        if del_tag:
            original_price = _to_int(del_tag.get_text())

        price_col = card.select_one("div.col-md-4")
        final_price_tag = price_col.find("h5") if price_col else None
        final_price: int = 0
        if final_price_tag:
            val = _to_int(final_price_tag.get_text())
            if val:
                final_price = val

        # Discount
        discount_tag = card.find("span", class_="badge-soft-success")
        discount_description: Optional[str] = discount_tag.get_text(strip=True) if discount_tag else None

        # Status
        status = _parse_status(card)

        # Sub-courses
        sub_courses: Optional[list[str]] = None
        sub_header = card.find("h5", string=re.compile("دوره های زیرمجموعه"))
        if sub_header:
            parent_div = sub_header.find_parent("div")
            sub_p = parent_div.find_next_sibling("p") if parent_div else None
            if not sub_p:
                parent = sub_header.find_parent()
                sub_p = parent.find_next("p") if parent else None
            if sub_p:
                raw = sub_p.get_text(separator=" ", strip=True)
                sub_courses = [s.strip() for s in re.findall(r"\(([^)]+)\)", raw)]

        return Course(
            id=course_id,
            department_id=department_id,
            name=name,
            instructor=instructor,
            schedule=schedule,
            start_date=start_date,
            duration_hours=duration_hours,
            capacity_remaining=capacity_remaining,
            original_price=original_price,
            final_price=final_price,
            discount_description=discount_description,
            status=status,
            sub_courses=sub_courses,
            url=url,
            start_note=start_note,
        )