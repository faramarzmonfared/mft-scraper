"""PostgreSQL storage layer for persisting scraped MFT data."""

import logging
import os

import psycopg2
from psycopg2.extensions import connection as PgConnection

from .schemas import Course, CourseDetail, Department

logger = logging.getLogger(__name__)


def _build_dsn() -> str:
    """Build a PostgreSQL DSN string from environment variables.

    Returns:
        PostgreSQL connection string.
    """
    return (
        f"host={os.environ['DB_HOST']} "
        f"port={os.environ['DB_PORT']} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )


class MFTStorage:
    """Handles all database operations for the MFT scraper.

    Uses upsert (INSERT ... ON CONFLICT) to support re-runs safely.

    Args:
        dsn: PostgreSQL connection string. If None, built from env vars.
    """

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or _build_dsn()
        self.conn: PgConnection | None = None

    def connect(self) -> None:
        """Open a connection to the PostgreSQL database."""
        logger.info("Connecting to database...")
        self.conn = psycopg2.connect(self.dsn)
        logger.info("Database connection established.")

    def close(self) -> None:
        """Close the database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("Database connection closed.")

    def create_tables(self) -> None:
        """Create database tables if they do not already exist."""
        assert self.conn, "Call connect() first."
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id          INTEGER PRIMARY KEY,
                    name        TEXT NOT NULL,
                    url         TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id                   INTEGER PRIMARY KEY,
                    department_id        INTEGER REFERENCES departments(id),
                    name                 TEXT NOT NULL,
                    instructor           TEXT,
                    schedule             TEXT,
                    start_date           TEXT,
                    start_note           TEXT,
                    duration_hours       INTEGER,
                    capacity_remaining   INTEGER,
                    original_price       BIGINT,
                    final_price          BIGINT,
                    discount_description TEXT,
                    status               TEXT,
                    sub_courses          TEXT[],
                    url                  TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS course_details (
                    course_id   INTEGER PRIMARY KEY REFERENCES courses(id),
                    description TEXT
                );
            """)
        self.conn.commit()
        logger.info("Tables verified/created.")

    def save_department(self, dept: Department) -> None:
        """Upsert a Department record.

        Args:
            dept: Department schema object.
        """
        assert self.conn, "Call connect() first."
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO departments (id, name, url)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                    SET name = EXCLUDED.name,
                        url  = EXCLUDED.url;
            """, (dept.id, dept.name, dept.url))
        self.conn.commit()
        logger.debug("Saved department id=%d", dept.id)

    def save_course(self, course: Course) -> None:
        """Upsert a Course record.

        Args:
            course: Course schema object.
        """
        assert self.conn, "Call connect() first."
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO courses (
                    id, department_id, name, instructor, schedule,
                    start_date, start_note, duration_hours, capacity_remaining,
                    original_price, final_price, discount_description,
                    status, sub_courses, url
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET
                    department_id        = EXCLUDED.department_id,
                    name                 = EXCLUDED.name,
                    instructor           = EXCLUDED.instructor,
                    schedule             = EXCLUDED.schedule,
                    start_date           = EXCLUDED.start_date,
                    start_note           = EXCLUDED.start_note,
                    duration_hours       = EXCLUDED.duration_hours,
                    capacity_remaining   = EXCLUDED.capacity_remaining,
                    original_price       = EXCLUDED.original_price,
                    final_price          = EXCLUDED.final_price,
                    discount_description = EXCLUDED.discount_description,
                    status               = EXCLUDED.status,
                    sub_courses          = EXCLUDED.sub_courses,
                    url                  = EXCLUDED.url;
            """, (
                course.id, course.department_id, course.name, course.instructor,
                course.schedule, course.start_date, course.start_note,
                course.duration_hours, course.capacity_remaining,
                course.original_price, course.final_price,
                course.discount_description, course.status,
                course.sub_courses, course.url,
            ))
        self.conn.commit()
        logger.debug("Saved course id=%d", course.id)

    def save_course_detail(self, detail: CourseDetail) -> None:
        """Upsert a CourseDetail record.

        Args:
            detail: CourseDetail schema object.
        """
        assert self.conn, "Call connect() first."
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO course_details (course_id, description)
                VALUES (%s, %s)
                ON CONFLICT (course_id) DO UPDATE
                    SET description = EXCLUDED.description;
            """, (detail.course_id, detail.description))
        self.conn.commit()
        logger.debug("Saved course detail for course_id=%d", detail.course_id)
        