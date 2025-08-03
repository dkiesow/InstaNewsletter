from transformers import pipeline, AutoTokenizer
from newspaper import Article
from newspaper.article import ArticleException
import re
import sqlite3
import os
import requests
from bs4 import BeautifulSoup

def detect_device():
    try:
        import torch
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("Auto-detected MPS device (device='mps')")
            return "mps"
        elif torch.cuda.is_available():
            print("Auto-detected CUDA device (device=0)")
            return 0
        else:
            print("Auto-detected CPU device (device=-1)")
            return -1
    except ImportError:
        print("Torch not installed, defaulting to CPU (device=-1)")
        return -1

def get_summarizer_and_tokenizer(device):
    MODEL_NAME = "facebook/bart-large-cnn"
    if device == "mps":
        summarizer = pipeline("summarization", model=MODEL_NAME, device_map={"": "mps"})
    else:
        summarizer = pipeline("summarization", model=MODEL_NAME, device=device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    return summarizer, tokenizer

def extract_source_name(url):
    try:
        # Use stealth headers to appear as a real browser
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Try Open Graph site name
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            return og_site["content"].strip()
        # Try Twitter site
        twitter_site = soup.find("meta", attrs={"name": "twitter:site"})
        if twitter_site and twitter_site.get("content"):
            return twitter_site["content"].strip().lstrip('@')
        # Try <title>
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        # Fallback to domain
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception as e:
        print(f"Error extracting source name: {e}")
        from urllib.parse import urlparse
        return urlparse(url).netloc

def process_article(article_info, summarizer, tokenizer, summary_max_words):
    print(f"Processing article: {article_info['url']}")  # Debug print
    # Extract source/publication name before processing
    publication_name = extract_source_name(article_info['url'])
    print(f"Extracted source: {publication_name}")  # Debug print
    article = Article(article_info['url'])
    try:
        article.download()
        article.parse()
        text = article.text or ""
        inputs = tokenizer(
            text,
            max_length=1024,
            truncation=True,
            return_tensors="pt",
            add_special_tokens=True
        )
        input_ids = inputs["input_ids"][0]
        truncated_text = tokenizer.decode(input_ids, skip_special_tokens=True)
        if len(truncated_text.split()) < 30:
            summary = truncated_text.strip()
        else:
            summary_outputs = summarizer(
                truncated_text,
                max_length=summary_max_words,
                min_length=max(20, summary_max_words // 2),
                do_sample=False
            )
            summary = summary_outputs[0]['summary_text'].strip()
            summary_words = summary.split()
            if len(summary_words) > summary_max_words:
                sentences = re.split(r'(?<=[.!?])\s+', summary)
                final_summary = []
                word_count = 0
                for sentence in sentences:
                    sentence_words = sentence.split()
                    final_summary.append(sentence)
                    word_count += len(sentence_words)
                    if word_count >= summary_max_words:
                        break
                summary = " ".join(final_summary).strip()
            sentences = re.split(r'(?<=[.!?])\s+', summary)
            while sentences and not re.search(r'[.!?]$', sentences[-1]):
                sentences.pop()
            summary = " ".join(sentences).strip()
        print("Article processed successfully.")  # Debug print

        return {
            "headline": article_info['title'].replace('\n', ' ').replace('\r', ' '),
            "body": text,
            "author": ", ".join(article.authors) if article.authors else "",
            "publication_date": article_info.get('published', ''),
            "publication_name": publication_name,
            "source": publication_name,
            "summary": summary,
            "url": article_info['url']
        }
    except ArticleException:
        print("Failed to process article.")  # Debug print
        return None

def export_to_markdown(records, export_path, summary_headline=""):
    print("Exporting records to markdown...")  # Debug print
    import datetime
    from config import NEWSLETTER_HEADLINE, APPEND_DATE_TO_HEADLINE, INCLUDE_DISCLAIMER, DISCLAIMER_TEXT
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    headline_date = datetime.datetime.now().strftime("%A %B %d")
    filename = os.path.join(export_path, f"newsletter_{date_str}.md")
    with open(filename, "w", encoding="utf-8") as f:
        # Compose the top headline with the summary headline if present
        top_headline = NEWSLETTER_HEADLINE
        if summary_headline:
            top_headline = f"{NEWSLETTER_HEADLINE} {summary_headline}"
        if APPEND_DATE_TO_HEADLINE:
            f.write(f"# {top_headline} {headline_date}\n\n")
        else:
            f.write(f"# {top_headline}\n\n")
        for idx, rec in enumerate(records):
            headline = rec['headline'].replace('\n', ' ').replace('\r', ' ')
            headline = headline.replace('[', '\\[').replace(']', '\\]')
            print(f"Markdown headline: {headline}")  # Debug print to check truncation
            # Headline as a link, then two spaces and newline
            f.write(f"[{headline}]({rec['url']})  \n")
            # Source, hyphen, pubdate (mm/dd/yy), then two spaces and newline
            pubdate = rec['publication_date']
            try:
                pubdate_fmt = datetime.datetime.strptime(pubdate, "%Y-%m-%d").strftime("%m/%d/%y")
            except Exception:
                pubdate_fmt = pubdate
            f.write(f"{rec['source']} - {pubdate_fmt}  \n")
            # Summary, then newline
            f.write(f"{rec['summary']}\n")
            # Add an additional newline before the section separator
            f.write("\n---\n\n")
        # Add disclaimer at the bottom if configured
        if INCLUDE_DISCLAIMER and DISCLAIMER_TEXT:
            f.write(f"{DISCLAIMER_TEXT}\n")
    print(f"Exported to {filename}")
import feedparser
import datetime
import html
from newsletter.db import get_existing_urls

def fetch_instapaper_articles(rss_url, db_path, max_articles):
    print("Fetching articles from Instapaper RSS feed...")  # Debug print
    feed = feedparser.parse(rss_url)
    since = datetime.datetime.now() - datetime.timedelta(days=7)
    recent = []
    existing_urls = get_existing_urls(db_path)
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
            })
    print(f"Fetched {len(recent[:max_articles])} articles for selection.")  # Debug print
    return recent[:max_articles]
