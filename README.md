# Newsletter

A Python application for creating newsletters from your Instapaper (or any) RSS feed. It fetches recent articles, allows you to select which to include, summarizes them using a Hugging Face model, and exports the results to both a SQLite database and a Markdown file.

## Features

- Fetches articles from any RSS feed (configurable via `config.py`).
- Only includes articles from the past 7 days (configurable).
- Skips articles already processed (by URL, tracked in the database).
- Presents headlines in a multi-select GUI (Tkinter).
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

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   For Apple Silicon/MPS support, ensure `torch>=1.12` is installed.

## Configuration

1. Copy `newsletter/config_template.py` to `newsletter/config.py`:

   ```bash
   cp newsletter/config_template.py newsletter/config.py
   ```

2. Edit `newsletter/config.py` to set your preferences:

   ```python
   RSS_URL = "https://www.instapaper.com/rss/your_feed_id/your_secret"
   DB_PATH = "newsletter.sqlite3"
   EXPORT_PATH = "/path/to/export"
   MAX_ARTICLES_FOR_SELECTION = 30  # Maximum number of articles to present for selection
   SUMMARY_MAX_WORDS = 100          # Maximum number of words in the summary
   DAYS_BACK = 7                    # Only include articles from the past N days
   HUGGINGFACE_MODEL = "facebook/bart-large-cnn"  # Model for summarization
   ```

   - `RSS_URL`: Your RSS feed URL.
   - `DB_PATH`: Path to the SQLite database file.
   - `EXPORT_PATH`: Directory where Markdown files will be saved.
   - `MAX_ARTICLES_FOR_SELECTION`: Maximum number of articles to show in the selection UI.
   - `SUMMARY_MAX_WORDS`: Maximum number of words in the summary (summary will end at the nearest sentence boundary).
   - `DAYS_BACK`: Number of days to look back for articles.
   - `HUGGINGFACE_MODEL`: Hugging Face model to use for summarization.

**Note:**  
Do not commit your `config.py` or database/markdown files; they are excluded by `.gitignore`.

## Usage

Run the main module:

```bash
python -m newsletter.main
```

- Select articles from the UI.
- Summaries and metadata are saved to the database and exported to a Markdown file named `newsletter_YYYYMMDD.md` in the export directory.

## Dependencies

- `feedparser`
- `newspaper3k`
- `lxml`
- `lxml_html_clean`
- `transformers`
- `torch`
- `inflect`
- `tkinter` (standard with Python)
- `sqlite3` (standard with Python)

**Environment:**
- Python 3.8+
- macOS, Linux, or Windows
- For Apple Silicon/MPS support, ensure `torch>=1.12` is installed.

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
setup.py
.gitignore
```

## License

MIT License
