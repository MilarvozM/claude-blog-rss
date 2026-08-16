"""Generate RSS 2.0 feed from post dicts.

Modified from the original upstream feed.py (anthropic-rss):
instead of embedding the full article text in each entry, each item
now only carries title + tags + link, plus the post's header
illustration as a media image. You see what's new and what tags it's
under, and decide yourself whether to click through.
"""

import os
from datetime import datetime, timezone

from feedgen.feed import FeedGenerator

FEED_TITLE = "Claude Blog (unofficial, headlines only)"
FEED_DESCRIPTION = (
    "Unofficial RSS feed for https://claude.com/blog. "
    "Titles and tags only, no article text. Content © Anthropic."
)
FEED_LINK = "https://claude.com/blog"
FEED_LANGUAGE = "en"

# Override via FEED_URL env var (set to your own GitHub Pages URL once known)
_DEFAULT_FEED_URL = "https://MilarvozM.github.io/claude-blog-rss/rss.xml"


def render(posts: list[dict], feed_url: str | None = None) -> str:
    """Render posts (most-recent-first) to RSS 2.0 XML string."""
    feed_url = feed_url or os.environ.get("FEED_URL", _DEFAULT_FEED_URL)

    fg = FeedGenerator()
    # Must be loaded before the first add_entry() or entries have no .media
    fg.load_extension("media")
    fg.id(feed_url)
    fg.title(FEED_TITLE)
    fg.description(FEED_DESCRIPTION)
    fg.link(href=FEED_LINK, rel="alternate")
    fg.link(href=feed_url, rel="self")
    fg.language(FEED_LANGUAGE)

    # feedgen.add_entry() prepends, so iterate oldest-first to get newest-first output
    sorted_posts = sorted(
        posts,
        key=lambda p: p.get("pub_date") or "",
        reverse=False,
    )

    for post in sorted_posts:
        fe = fg.add_entry()
        fe.id(post["url"])
        fe.title(post["title"] or post["slug"])
        fe.link(href=post["url"])

        if post.get("pub_date"):
            try:
                dt = datetime.fromisoformat(post["pub_date"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                fe.published(dt)
                fe.updated(dt)
            except ValueError:
                pass

        categories = post.get("categories") or []
        for cat in categories:
            fe.category({"term": cat})

        cat_label = ", ".join(categories) if categories else "Uncategorized"

        # No article body, just the tags line, mirrored in both fields so it
        # works regardless of which one a given reader displays.
        summary = f"Tags: {cat_label}"
        fe.description(summary)
        fe.content(f"<p>{summary}</p>", type="html")

        # The post's header illustration, as siblings of the text fields so
        # readers get a thumbnail without the preview text changing.
        image = post.get("image")
        if image:
            fe.media.content({"url": image, "medium": "image"})
            fe.media.thumbnail({"url": image})

    return fg.rss_str(pretty=True).decode("utf-8")
