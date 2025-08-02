# Newsletter

A Python application for managing and sending newsletters.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `newsletter/config.py` to set your Instapaper RSS feed URL, database path, and export path.

## Usage

```bash
python -m newsletter.main
```

- Select articles from the past 7 days in the UI.
- Processed articles are saved to the database and exported as a Markdown file.
