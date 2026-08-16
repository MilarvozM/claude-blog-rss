"""Tests for feed.py."""

import xml.etree.ElementTree as ET

from src.feed import render

MEDIA = "http://search.yahoo.com/mrss/"
CONTENT = "http://purl.org/rss/1.0/modules/content/"


def _make_posts(n: int) -> list[dict]:
    return [
        {
            "slug": f"post-{i}",
            "url": f"https://claude.com/blog/post-{i}",
            "title": f"Post {i}",
            "date_str": f"January {i + 1}, 2026",
            "pub_date": f"2026-01-{i + 1:02d}T00:00:00+00:00",
            "categories": ["Test"],
            "image": f"https://cdn.example/{i}-1000x1000.svg",
            "html_body": f"<p>Content of post {i}</p>",
        }
        for i in range(n)
    ]


def test_feed_is_valid_xml():
    xml_str = render(_make_posts(3))
    root = ET.fromstring(xml_str)
    assert root.tag == "rss"


def test_feed_version():
    xml_str = render(_make_posts(1))
    root = ET.fromstring(xml_str)
    assert root.attrib.get("version") == "2.0"


def test_feed_item_count_capped_at_20():
    posts = _make_posts(30)
    xml_str = render(posts[:20])
    root = ET.fromstring(xml_str)
    channel = root.find("channel")
    items = channel.findall("item")
    assert len(items) == 20


def test_feed_item_has_required_fields():
    xml_str = render(_make_posts(1))
    root = ET.fromstring(xml_str)
    item = root.find("channel/item")
    assert item.find("title").text == "Post 0"
    assert item.find("link").text is not None
    assert item.find("guid").text is not None


def test_feed_sorted_newest_first():
    posts = _make_posts(5)
    xml_str = render(posts)
    root = ET.fromstring(xml_str)
    channel = root.find("channel")
    items = channel.findall("item")
    titles = [item.find("title").text for item in items]
    # Post 4 (Jan 5) should come before Post 0 (Jan 1)
    assert titles.index("Post 4") < titles.index("Post 0")


def test_feed_item_has_media_image():
    xml_str = render(_make_posts(1))
    root = ET.fromstring(xml_str)
    item = root.find("channel/item")
    assert item.find(f".//{{{MEDIA}}}content").attrib["url"] == (
        "https://cdn.example/0-1000x1000.svg"
    )
    assert item.find(f".//{{{MEDIA}}}thumbnail").attrib["url"] == (
        "https://cdn.example/0-1000x1000.svg"
    )


def test_feed_item_without_image_key_emits_no_media():
    """Posts stored before the image key existed must still render."""
    posts = _make_posts(1)
    del posts[0]["image"]
    xml_str = render(posts)
    root = ET.fromstring(xml_str)
    item = root.find("channel/item")
    assert item.find(f".//{{{MEDIA}}}content") is None
    assert item.find(f".//{{{MEDIA}}}thumbnail") is None


def test_feed_preview_text_is_tags_only():
    """Regression lock: this is what Feedly shows as the preview text."""
    xml_str = render(_make_posts(1))
    root = ET.fromstring(xml_str)
    item = root.find("channel/item")
    assert item.find("description").text == "Tags: Test"
    assert item.find(f"{{{CONTENT}}}encoded").text == "<p>Tags: Test</p>"


def test_feed_empty_posts():
    xml_str = render([])
    root = ET.fromstring(xml_str)
    channel = root.find("channel")
    assert len(channel.findall("item")) == 0
