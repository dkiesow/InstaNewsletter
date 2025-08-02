# Newsletter

A Python application for creating newsletters from your Instapaper RSS feed.  
It fetches recent articles, allows you to select which to include, summarizes them using a Hugging Face model, and exports the results to both a SQLite database and a Markdown file.

## Features

- Fetches articles from your Instapaper RSS feed (configurable).
- Only includes articles from the past 7 days. (configurable).
- Skips articles already processed (by URL).
- Presents headlines in a multi-select GUI.
- Summarizes articles using an abstractive Hugging Face model (BART).
- Summaries are capped at a configurable word count and end with a complete sentence.
- Stores publication name, headline, URL, author, publication date, and summary in a SQLite database.
- Exports selected articles to a Markdown file, one per session, with the format:

  ```
  [Headline](URL)
  publication name
  publication date
  Summary
  ```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `newsletter/config_template.py` to `newsletter/config.py` and edit the variables:

```python
INSTAPAPER_RSS_URL = "https://www.instapaper.com/rss/your_feed_id/your_secret"
DB_PATH = "newsletter.sqlite3"
EXPORT_PATH = "/path/to/export"
MAX_ARTICLES_FOR_SELECTION = 30  # Maximum number of articles to present for selection
SUMMARY_MAX_WORDS = 100          # Maximum number of words in the summary
```

- `INSTAPAPER_RSS_URL`: Your Instapaper RSS feed URL.
- `DB_PATH`: Path to the SQLite database file.
- `EXPORT_PATH`: Directory where Markdown files will be saved.
- `MAX_ARTICLES_FOR_SELECTION`: Maximum number of articles to show in the selection UI.
- `SUMMARY_MAX_WORDS`: Maximum number of words in the summary (summary will end at the nearest sentence boundary).

**Note:**  
Do not commit your `config.py` or database/markdown files; they are excluded by `.gitignore`.

## Usage

```bash
python -m newsletter.main
```

- Select articles from the UI.
- Summaries and metadata are saved to the database and exported to a Markdown file named `newsletter_YYYYMMDD.md`.

## Dependencies

- `feedparser`
- `newspaper`
- `lxml`
- `lxml_html_clean`
- `transformers`
- `torch`
- `tkinter` (standard with Python)
- `sqlite3` (standard with Python)

For Apple Silicon/MPS support, ensure `torch>=1.12` is installed.

## Directory Structure

```
newsletter/
    __init__.py
    main.py
    config.py
    config_template.py
    db.py
    rss.py
    ui.py
    summarize.py
requirements.txt
README.md
.gitignore
```

## License

MIT License
