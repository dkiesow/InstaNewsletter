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

        # Aggregate all new summaries and summarize them in headline style
        all_summaries = " ".join([rec["summary"] for rec in processed_records if rec.get("summary")])
        summary_headline = ""
        if all_summaries.strip():
            print("Concatenated article summaries for headline:")
            print(all_summaries)  # Debug print of concatenated summaries
            print("Generating a headline for article summaries...")
            prompt = (
                "Write a simple headline for this text: " + all_summaries
            )
            agg_summary = summarizer(
                prompt,
                max_length=60,
                min_length=10,
                do_sample=False
            )[0]['summary_text'].strip()
            # Ensure the headline is at most 60 characters
            if len(agg_summary) > 60:
                agg_summary = agg_summary[:60]
            # Trim back to the previous sentence stop if incomplete
            import re
            last_punct = max(agg_summary.rfind('.'), agg_summary.rfind('!'), agg_summary.rfind('?'))
            if last_punct != -1 and last_punct < len(agg_summary) - 1:
                agg_summary = agg_summary[:last_punct+1].strip()
            summary_headline = agg_summary
            print(f"Headline-style aggregate summary (<=60 chars): {summary_headline}")
        else:
            summary_headline = ""
        # Pass the summary_headline to export_to_markdown
        export_to_markdown(processed_records, EXPORT_PATH, summary_headline=summary_headline)
    else:
        print("No articles could be processed.")

if __name__ == "__main__":
    print("Welcome to the Newsletter application!")
    main()
