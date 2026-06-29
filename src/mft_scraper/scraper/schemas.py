"""Pydantic schemas for MFT Shiraz scraper data models.

These schemas define the data contract between the scraping layer
and the rest of the RAG system. If the data source changes,
only the scraper layer needs to be updated.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CourseStatus(str, Enum):
    """Enrollment status of a course."""

    ENROLLING = "enrolling"
    FILLING = "filling"
    FULL = "full"


class Department(BaseModel):
    """Represents a department from the main listing page."""

    id: int = Field(..., description="Department ID extracted from URL")
    name: str = Field(..., description="Department name")
    url: str = Field(..., description="Full URL to department page")


class Course(BaseModel):
    """Represents a course listed within a department page."""

    id: int = Field(..., description="Course ID extracted from URL")
    department_id: int = Field(..., description="Parent department ID")
    name: str = Field(..., description="Course name including group number")
    instructor: str = Field(..., description="Instructor full name")
    schedule: str = Field(..., description="Raw schedule text e.g. 'دوشنبه‌ها ۱۶:۰۰ الی ۲۱:۰۰'")
    duration_hours: int = Field(..., description="Total course duration in hours")
    capacity_remaining: int = Field(..., description="Number of remaining seats")
    original_price: Optional[int] = Field(None, description="Original price in Rials before discount")
    final_price: int = Field(..., description="Final price in Rials")
    discount_description: Optional[str] = Field(None, description="Discount badge text if present")
    status: CourseStatus = Field(..., description="Current enrollment status")
    sub_courses: Optional[list[str]] = Field(None, description="List of sub-course names if present")


class CourseDetail(BaseModel):
    """Represents detailed information from an individual course page."""

    course_id: int = Field(..., description="Course ID matching Course.id")
    prerequisites: Optional[str] = Field(None, description="Prerequisites text if present")
    syllabus: str = Field(..., description="Full syllabus and description block as raw text")
    