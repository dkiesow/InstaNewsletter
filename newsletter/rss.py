import feedparser
import datetime
import html
from newsletter.db import get_existing_urls
from config import MAX_ARTICLE_AGE_DAYS

def fetch_instapaper_articles(rss_urls, db_path, max_articles):
    print("Fetching articles from RSS feed...")  # Debug print
    since = datetime.datetime.now() - datetime.timedelta(days=MAX_ARTICLE_AGE_DAYS)
    recent = []
    existing_urls = get_existing_urls(db_path)
    if not isinstance(rss_urls, list):
        rss_urls = [rss_urls]
    for rss_url in rss_urls:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime.datetime.fromtimestamp(
                    int(datetime.datetime(*entry.published_parsed[:6]).timestamp())
                )
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub_date = datetime.datetime.fromtimestamp(
                    int(datetime.datetime(*entry.updated_parsed[:6]).timestamp())
                )
            else:
                pub_date = None
            if entry.link in existing_urls:
                continue
            if pub_date and pub_date >= since:
                decoded_title = html.unescape(entry.title)
                recent.append({
                    "title": decoded_title,
                    "url": entry.link,
                    "published": pub_date.strftime("%Y-%m-%d"),
                    "pub_date_obj": pub_date,  # For sorting
                })
    # Sort all articles by pub_date_obj descending, then limit to max_articles
    recent.sort(key=lambda x: x["pub_date_obj"], reverse=True)
    # Remove the helper field before returning
    for r in recent:
        r.pop("pub_date_obj", None)
    print(f"Fetched {len(recent[:max_articles])} articles for selection.")  # Debug print
    return recent[:max_articles]
