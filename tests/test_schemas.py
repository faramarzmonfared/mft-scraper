"""Tests for Pydantic schemas."""

import pytest

from mft_scraper.scraper.schemas import Course, CourseDetail, CourseStatus, Department


def test_department_creation():
    dept = Department(id=1, name="Computer IT", url="https://example.com/department/1")
    assert dept.id == 1
    assert dept.name == "Computer IT"
    assert dept.url == "https://example.com/department/1"


def test_course_status_values():
    assert CourseStatus.ENROLLING == "enrolling"
    assert CourseStatus.FILLING == "filling"
    assert CourseStatus.FULL == "full"


def test_course_optional_fields_default_to_none():
    course = Course(
        id=100,
        department_id=1,
        name="Test Course",
        instructor="John Doe",
        schedule="Monday 09:00-12:00",
        duration_hours=30,
        capacity_remaining=5,
        final_price=5000000,
        status=CourseStatus.ENROLLING,
        url="https://example.com/public/class/100",
    )
    assert course.original_price is None
    assert course.discount_description is None
    assert course.start_date is None
    assert course.start_note is None
    assert course.sub_courses is None


def test_course_detail_creation():
    detail = CourseDetail(course_id=100, description="Course syllabus content here.")
    assert detail.course_id == 100
    assert "syllabus" in detail.description
