import tkinter as tk
from tkinter import MULTIPLE, Listbox, Scrollbar, END
from urllib.parse import urlparse

def select_articles_gui(articles):
    print("Presenting selection UI for articles...")  # Debug print
    selected_indices = []

    def on_ok():
        nonlocal selected_indices
        selected_indices = listbox.curselection()
        root.destroy()

    root = tk.Tk()
    root.title("Select Articles")

    # Dynamically set window size based on number of articles
    num_articles = len(articles)
    window_height = min(max(num_articles * 25, 300), 900)  # px
    window_width = 900
    root.geometry(f"{window_width}x{window_height}")

    # Main frame for listbox and scrollbar
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    listbox = Listbox(main_frame, selectmode=MULTIPLE, width=100, height=min(num_articles, 40))
    scrollbar = Scrollbar(main_frame)
    scrollbar.pack(side="right", fill="y")
    listbox.pack(side="left", fill="both", expand=True)
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    for idx, article in enumerate(articles):
        # Extract site name or TLD from URL
        parsed_url = urlparse(article['url'])
        site = parsed_url.netloc
        # Show the title and site/TLD
        display_text = f"{article['title']}  [{site}]"
        listbox.insert(END, display_text)

    # Bottom frame for OK button, always visible
    button_frame = tk.Frame(root)
    button_frame.pack(fill="x", side="bottom")
    btn = tk.Button(button_frame, text="OK", command=on_ok)
    btn.pack(pady=8)

    root.mainloop()
    selected = [articles[i] for i in selected_indices]
    print(f"{len(selected_indices)} articles selected.")  # Debug print (after selection)
    return selected
