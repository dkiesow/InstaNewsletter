RSS_URL = [
    "https://www.instapaper.com/rss/your_feed_id/your_secret",
    # "https://another.feed.url/rss",
]
DB_PATH = "newsletter.sqlite3"
EXPORT_PATH = "/path/to/export"
MAX_ARTICLES_FOR_SELECTION = 30  # Maximum number of articles to present for selection
SUMMARY_MAX_WORDS = 100  # Maximum number of words in the summary
MAX_ARTICLE_AGE_DAYS = 7  # Maximum age of articles (in days) to fetch from RSS
NEWSLETTER_HEADLINE = "Your Newsletter Headline Here"  # Headline for the top of the exported markdown file
APPEND_DATE_TO_HEADLINE = True  # If True, append the date after the newsletter headline in the markdown export
INCLUDE_DISCLAIMER = False  # If True, include disclaimer at the bottom of the markdown export
DISCLAIMER_TEXT = "Notes for readers. I mention that the summaries are GenAI created"  # The disclaimer text to include
