from transformers import pipeline, AutoTokenizer
from newspaper import Article
from newspaper.article import ArticleException
import re
import sqlite3
import os

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

def process_article(article_info, summarizer, tokenizer, summary_max_words):
    print(f"Processing article: {article_info['url']}")  # Debug print
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
            "publication_name": article.source_url or "",
            "summary": summary,
            "url": article_info['url']
        }
    except ArticleException:
        print("Failed to process article.")  # Debug print
        return None

def export_to_markdown(records, export_path):
    print("Exporting records to markdown...")  # Debug print
    import datetime
    from config import NEWSLETTER_HEADLINE
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = os.path.join(export_path, f"newsletter_{date_str}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {NEWSLETTER_HEADLINE}\n\n")
        for rec in records:
            headline = rec['headline'].replace('\n', ' ').replace('\r', ' ')
            headline = headline.replace('[', '\\[').replace(']', '\\]')
            print(f"Markdown headline: {headline}")  # Debug print to check truncation
            try:
                conn = sqlite3.connect(":memory:")  # No DB check here, just for compatibility
                conn.close()
            except Exception as e:
                print(f"DB headline check error: {e}")
            f.write(f"[{headline}]({rec['url']})\n")
            f.write(f"{rec['publication_name']}\n")
            f.write(f"{rec['publication_date']}\n")
            f.write(f"{rec['summary']}\n\n")
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
