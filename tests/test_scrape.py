"""Tests for scrape.py using local HTML fixtures (no network)."""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from src.scrape import (
    _extract_detail,
    _extract_detail_list,
    _extract_hero_image,
    _parse_date,
)

FIXTURES = Path(__file__).parent / "fixtures"


def listing_html() -> str:
    return (FIXTURES / "blog_listing.html").read_text()


def post_html() -> str:
    return (FIXTURES / "post_example.html").read_text()


# ── listing page ──────────────────────────────────────────────────────────────

def test_listing_finds_slugs():
    """At least 10 unique slugs on the listing page."""
    import re
    html = listing_html()
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all(
        "a",
        attrs={"data-cta": "Blog page", "href": re.compile(r"^/blog/[^/]+$")},
    )
    seen = {l["href"][len("/blog/"):] for l in links}
    assert len(seen) >= 10, f"Expected >=10 slugs, got {len(seen)}"


def test_listing_unique_slugs_at_least_10():
    """Listing page has at least 10 *unique* slugs (marquee+grid may repeat the same slug)."""
    import re
    html = listing_html()
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all(
        "a",
        attrs={"data-cta": "Blog page", "href": re.compile(r"^/blog/[^/]+$")},
    )
    unique = {l["href"][len("/blog/"):] for l in links}
    assert len(unique) >= 10, f"Expected >=10 unique slugs, got {len(unique)}"


# ── post detail page ──────────────────────────────────────────────────────────

def test_post_extracts_title():
    soup = BeautifulSoup(post_html(), "lxml")
    h1 = soup.find("h1")
    assert h1 is not None
    assert len(h1.get_text(strip=True)) > 5


def test_post_extracts_date():
    soup = BeautifulSoup(post_html(), "lxml")
    date_str = _extract_detail(soup, "Date")
    assert date_str, "Date not found"
    dt = _parse_date(date_str)
    assert dt is not None, f"Could not parse date: {date_str!r}"
    assert dt.year >= 2024


def test_post_extracts_categories():
    soup = BeautifulSoup(post_html(), "lxml")
    cats = _extract_detail_list(soup, "Category")
    assert len(cats) >= 1, "Expected at least one category"


def test_post_extracts_body_html():
    soup = BeautifulSoup(post_html(), "lxml")
    body_div = soup.find("div", class_="blog_post_content_wrap")
    assert body_div is not None, "blog_post_content_wrap not found"
    text = body_div.get_text()
    assert len(text) > 200, "Article body seems too short"


def test_post_extracts_hero_image():
    soup = BeautifulSoup(post_html(), "lxml")
    src = _extract_hero_image(soup)
    assert src.startswith("https://"), f"Hero image not found: {src!r}"
    assert src.endswith(".svg")


def test_extract_hero_image_absent():
    soup = BeautifulSoup("<div><img src='https://e/other.svg'></div>", "lxml")
    assert _extract_hero_image(soup) == ""


# ── date parser ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("date_str,year", [
    ("April 14, 2026", 2026),
    ("Apr 20, 2026", 2026),
    ("January 1, 2024", 2024),
])
def test_parse_date_formats(date_str, year):
    dt = _parse_date(date_str)
    assert dt is not None
    assert dt.year == year


def test_parse_date_invalid():
    assert _parse_date("") is None
    assert _parse_date("not a date") is None
