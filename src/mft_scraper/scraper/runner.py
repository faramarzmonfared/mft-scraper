"""Orchestrator that coordinates scraping and storage for MFT Shiraz."""

import logging
import os

from dotenv import load_dotenv

from .course_detail import CourseDetailScraper
from .courses import CourseScraper
from .departments import DepartmentScraper
from .storage import MFTStorage

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://my.mftshiraz.ir"


def run() -> None:
    """Run the full MFT scraping pipeline.

    Scrapes departments, courses, and course details sequentially,
    persisting each record to PostgreSQL. Errors on individual items
    are logged and skipped to allow the pipeline to continue.
    """
    db = MFTStorage()
    db.connect()
    db.create_tables()

    dept_scraper = DepartmentScraper(base_url=BASE_URL)
    course_scraper = CourseScraper(base_url=BASE_URL)
    detail_scraper = CourseDetailScraper(base_url=BASE_URL, delay=2)

    # Step 1: scrape and save departments
    logger.info("Starting department scraping...")
    departments = dept_scraper.run(f"{BASE_URL}/public/")
    for dept in departments:
        try:
            db.save_department(dept)
        except Exception as e:
            logger.error("Failed to save department id=%d: %s", dept.id, e)

    logger.info("Departments done: %d", len(departments))

    # Step 2: scrape and save courses per department
    for dept in departments:
        logger.info("Scraping courses for department: %s (id=%d)", dept.name, dept.id)
        try:
            courses = course_scraper.run(dept.url)
        except Exception as e:
            logger.error("Failed to scrape department id=%d: %s", dept.id, e)
            continue

        for course in courses:
            try:
                db.save_course(course)
            except Exception as e:
                logger.error("Failed to save course id=%d: %s", course.id, e)

        logger.info("Courses done for department %d: %d", dept.id, len(courses))

        # Step 3: scrape and save course details
        for course in courses:
            try:
                details = detail_scraper.scrape(course.url, course.id)
                for detail in details:
                    db.save_course_detail(detail)
            except Exception as e:
                logger.error("Failed to scrape/save detail for course id=%d: %s", course.id, e)

    db.close()
    logger.info("Scraping pipeline completed.")


if __name__ == "__main__":
    run()
