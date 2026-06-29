# MFT Scraper

A modular web scraper for the [MFT Shiraz](https://my.mftshiraz.ir) course catalog, designed as the data ingestion layer for a RAG-based chatbot system.

## Architecture

The scraper is built as a standalone Python package, fully independent of any web framework. This ensures that if the data source changes (e.g. from scraping to a direct database feed), only the ingestion layer needs to be updated — the rest of the RAG system remains untouched.

```
src/mft_scraper/scraper/
├── base.py           # Abstract base scraper with retry logic
├── departments.py    # Scrapes department list
├── courses.py        # Scrapes course list per department
├── course_detail.py  # Scrapes individual course description
├── schemas.py        # Pydantic data contracts
├── storage.py        # PostgreSQL persistence layer
└── runner.py         # Orchestrator / pipeline entry point
```

## Installation

Requires Python 3.11+ and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/faramarzmonfared/mft-scraper.git
cd mft-scraper
poetry install
```

## Configuration

Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:

```bash
cp .env.example .env
```

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=
DB_USER=
DB_PASSWORD=
```

## Usage

```bash
poetry run python -m mft_scraper.scraper.runner
```

The pipeline will:
1. Scrape all departments from the main page
2. Scrape the course list for each department
3. Scrape the detail page for each course
4. Persist all data to PostgreSQL using upsert — safe to re-run

## Database Schema

```sql
departments (id, name, url)

courses (
    id, department_id, name, instructor,
    schedule, start_date, start_note,
    duration_hours, capacity_remaining,
    original_price, final_price, discount_description,
    status, sub_courses, url
)

course_details (course_id, description)
```

## Data Contract

All scraped data is validated against [Pydantic](https://docs.pydantic.dev/) schemas defined in `schemas.py`. This acts as the contract between the scraping layer and the downstream RAG system.

## License

MIT