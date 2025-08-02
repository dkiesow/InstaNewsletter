import os
import sys
import datetime
from queue import Queue
from config import INSTAPAPER_RSS_URL, DB_PATH, EXPORT_PATH, MAX_ARTICLES_FOR_SELECTION, SUMMARY_MAX_WORDS

from newsletter.db import (
    ensure_model_table_and_get_device,
    ensure_models_table_and_get_device,
    save_device_to_model_table,
    save_device_to_models_table,
    save_to_db,
    get_existing_urls,
)
from newsletter.rss import fetch_instapaper_articles
from newsletter.ui import select_articles_gui
from newsletter.summarize import (
    detect_device,
    get_summarizer_and_tokenizer,
    process_article,
    export_to_markdown,
)

def main():
    print("Starting newsletter processing session...")  # Debug print

    # Device/model selection logic
    device = ensure_models_table_and_get_device(DB_PATH)
    if device is None:
        device = ensure_model_table_and_get_device(DB_PATH)
    if device is None:
        device = detect_device()
        save_device_to_models_table(DB_PATH, device)
        save_device_to_model_table(DB_PATH, device)

    summarizer, tokenizer = get_summarizer_and_tokenizer(device)

    articles = fetch_instapaper_articles(
        INSTAPAPER_RSS_URL, DB_PATH, MAX_ARTICLES_FOR_SELECTION
    )
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
        data = process_article(art, summarizer, tokenizer, SUMMARY_MAX_WORDS)
        if data:
            processed_records.append(data)
        q.task_done()

    if processed_records:
        save_to_db(DB_PATH, processed_records)
        export_to_markdown(processed_records, EXPORT_PATH)
    else:
        print("No articles could be processed.")

if __name__ == "__main__":
    print("Welcome to the Newsletter application!")
    main()
