import os
import sys
import sqlite3
import datetime
from newspaper import Article
from newspaper.article import ArticleException
import feedparser
import tkinter as tk
from tkinter import MULTIPLE, Listbox, Scrollbar, END
from config import INSTAPAPER_RSS_URL, DB_PATH, EXPORT_PATH, MAX_ARTICLES_FOR_SELECTION, SUMMARY_MAX_WORDS
from queue import Queue
from transformers import pipeline, AutoTokenizer
import html  # For decoding HTML entities

def ensure_model_table_and_get_device():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create Model table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS Model (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Try to get device from Model table
    c.execute("SELECT value FROM Model WHERE key = 'cpu_model'")
    row = c.fetchone()
    device = None
    if row:
        try:
            device = int(row[0])
            print(f"Loaded device from Model table: {device}")
        except Exception:
            device = row[0]  # For string values like 'mps'
            print(f"Loaded device from Model table: {device}")
    conn.close()
    return device

def ensure_models_table_and_get_device():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Create Models table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS Models (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Try to get device from Models table
    c.execute("SELECT value FROM Models WHERE key = 'cpu_model'")
    row = c.fetchone()
    device = None
    if row:
        try:
            device = int(row[0])
            print(f"Loaded device from Models table: {device}")
        except Exception:
            device = row[0]  # For string values like 'mps'
            print(f"Loaded device from Models table: {device}")
    conn.close()
    return device

def save_device_to_model_table(device):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Model (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute("INSERT OR REPLACE INTO Model (key, value) VALUES (?, ?)", ('cpu_model', str(device)))
    conn.commit()
    conn.close()
    print(f"Saved device to Model table: {device}")

def save_device_to_models_table(device):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Models (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute("INSERT OR REPLACE INTO Models (key, value) VALUES (?, ?)", ('cpu_model', str(device)))
    conn.commit()
    conn.close()
    print(f"Saved device to Models table: {device}")

def detect_device():
    # Try to use MPS if available, else CUDA, else CPU
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

# Check Models table first, then Model table, then auto-detect
device = ensure_models_table_and_get_device()
if device is None:
    device = ensure_model_table_and_get_device()
if device is None:
    device = detect_device()
    save_device_to_models_table(device)
    save_device_to_model_table(device)

MODEL_NAME = "facebook/bart-large-cnn"

# Always pass device to the pipeline before initialization
if device == "mps":
    summarizer = pipeline("summarization", model=MODEL_NAME, device_map={"": "mps"})
else:
    summarizer = pipeline("summarization", model=MODEL_NAME, device=device)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def fetch_instapaper_articles():
    print("Fetching articles from Instapaper RSS feed...")  # Debug print
    feed = feedparser.parse(INSTAPAPER_RSS_URL)
    since = datetime.datetime.now() - datetime.timedelta(days=7)
    recent = []
    # Fetch URLs already in the DB to avoid duplicates
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_name TEXT,
        headline TEXT,
        url TEXT,
        author TEXT,
        publication_date TEXT,
        summary TEXT
    )''')
    c.execute("SELECT url FROM stories")
    existing_urls = set(row[0] for row in c.fetchall())
    conn.close()
    for entry in feed.entries:
        # Try to parse published date
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
        # Skip if URL already exists in DB
        if entry.link in existing_urls:
            continue
        if pub_date and pub_date >= since:
            # Decode HTML entities in the title
            decoded_title = html.unescape(entry.title)
            recent.append({
                "title": decoded_title,
                "url": entry.link,
                "published": pub_date.strftime("%Y-%m-%d"),
            })
    print(f"Fetched {len(recent[:MAX_ARTICLES_FOR_SELECTION])} articles for selection.")  # Debug print
    return recent[:MAX_ARTICLES_FOR_SELECTION]

def select_articles_gui(articles):
    print("Presenting selection UI for articles...")  # Debug print
    selected_indices = []

    def on_ok():
        nonlocal selected_indices
        selected_indices = listbox.curselection()
        root.destroy()

    root = tk.Tk()
    root.title("Select Articles")
    listbox = Listbox(root, selectmode=MULTIPLE, width=100)
    scrollbar = Scrollbar(root)
    scrollbar.pack(side="right", fill="y")
    listbox.pack(side="left", fill="both", expand=True)
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    for idx, article in enumerate(articles):
        # Escape problematic characters in headline for display
        safe_title = article['title'].replace("'", "\\'").replace('"', '\\"')
        listbox.insert(END, safe_title)

    btn = tk.Button(root, text="OK", command=on_ok)
    btn.pack()
    root.mainloop()
    selected = [articles[i] for i in selected_indices]
    print(f"{len(selected_indices)} articles selected.")  # Debug print (after selection)
    return selected

def process_article(article_info):
    # article_info: dict with keys 'title', 'url', 'published'
    print(f"Processing article: {article_info['url']}")  # Debug print
    article = Article(article_info['url'])
    try:
        article.download()
        article.parse()
        text = article.text or ""
        # Tokenize and truncate to model's max input length (1024 tokens for BART)
        inputs = tokenizer(
            text,
            max_length=1024,
            truncation=True,
            return_tensors="pt",
            add_special_tokens=True
        )
        input_ids = inputs["input_ids"][0]
        truncated_text = tokenizer.decode(input_ids, skip_special_tokens=True)
        # Use Hugging Face summarization pipeline (abstractive)
        if len(truncated_text.split()) < 30:
            summary = truncated_text.strip()
        else:
            summary_outputs = summarizer(
                truncated_text,
                max_length=SUMMARY_MAX_WORDS,
                min_length=max(20, SUMMARY_MAX_WORDS // 2),
                do_sample=False
            )
            summary = summary_outputs[0]['summary_text'].strip()
            # Ensure summary does not cut off mid-sentence and meets/exceeds SUMMARY_MAX_WORDS
            summary_words = summary.split()
            if len(summary_words) > SUMMARY_MAX_WORDS:
                import re
                sentences = re.split(r'(?<=[.!?])\s+', summary)
                final_summary = []
                word_count = 0
                for sentence in sentences:
                    sentence_words = sentence.split()
                    final_summary.append(sentence)
                    word_count += len(sentence_words)
                    if word_count >= SUMMARY_MAX_WORDS:
                        break
                summary = " ".join(final_summary).strip()
            # Post-process: ensure summary ends with a complete sentence
            import re
            sentences = re.split(r'(?<=[.!?])\s+', summary)
            while sentences and not re.search(r'[.!?]$', sentences[-1]):
                sentences.pop()
            summary = " ".join(sentences).strip()
        print("Article processed successfully.")  # Debug print
        # Only remove newlines from headline for storage, do not escape quotes
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

def main():
    print("Starting newsletter processing session...")  # Debug print
    articles = fetch_instapaper_articles()
    if not articles:
        print("No articles found from the past 7 days.")
        return
    selected = select_articles_gui(articles)
    if not selected:
        print("No articles selected.")
        return

    print("Queueing selected articles for processing...")  # Debug print
    q = Queue()
    for art in selected:
        q.put(art)

    processed_records = []
    while not q.empty():
        art = q.get()
        print(f"Processing headline: {art['title']}")  # Print headline before URL
        print(f"Processing URL: {art['url']}")         # Debug print
        data = process_article(art)
        if data:
            processed_records.append(data)
        q.task_done()

    if processed_records:
        save_to_db(processed_records)
        export_to_markdown(processed_records)
    else:
        print("No articles could be processed.")

def save_to_db(records):
    print(f"Saving {len(records)} records to the database...")  # Debug print
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_name TEXT,
        headline TEXT,
        url TEXT,
        author TEXT,
        publication_date TEXT,
        summary TEXT
    )''')
    # Fetch existing URLs to avoid duplicates
    c.execute("SELECT url FROM stories")
    existing_urls = set(row[0] for row in c.fetchall())
    for rec in records:
        db_headline = rec["headline"].replace('\n', ' ').replace('\r', ' ')
        if rec["url"] in existing_urls:
            continue
        c.execute('''INSERT INTO stories (publication_name, headline, url, author, publication_date, summary)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (rec["publication_name"], db_headline, rec["url"], rec["author"], rec["publication_date"], rec["summary"]))
    conn.commit()
    conn.close()
    print("Records saved to database.")  # Debug print

def export_to_markdown(records):
    print("Exporting records to markdown...")  # Debug print
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = os.path.join(EXPORT_PATH, f"newsletter_{date_str}.md")
    with open(filename, "w", encoding="utf-8") as f:
        for rec in records:
            # Unescape headline before writing to markdown, remove newlines, and escape [ and ] for markdown safety
            headline = rec['headline'].replace('\n', ' ').replace('\r', ' ')
            headline = headline.replace('[', '\\[').replace(']', '\\]')
            print(f"Markdown headline: {headline}")  # Debug print to check truncation
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT headline FROM stories WHERE headline = ?", (rec['headline'],))
                db_headline = c.fetchone()
                if db_headline:
                    print(f"DB headline: {db_headline[0]}")
                conn.close()
            except Exception as e:
                print(f"DB headline check error: {e}")
            f.write(f"[{headline}]({rec['url']})\n")
            f.write(f"{rec['publication_name']}\n")
            f.write(f"{rec['publication_date']}\n")
            f.write(f"{rec['summary']}\n\n")
    print(f"Exported to {filename}")

if __name__ == "__main__":
    print("Welcome to the Newsletter application!")
    main()
