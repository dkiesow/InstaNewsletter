import tkinter as tk
from tkinter import MULTIPLE, Listbox, Scrollbar, END

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
        safe_title = article['title'].replace("'", "\\'").replace('"', '\\"')
        listbox.insert(END, safe_title)

    btn = tk.Button(root, text="OK", command=on_ok)
    btn.pack()
    root.mainloop()
    selected = [articles[i] for i in selected_indices]
    print(f"{len(selected_indices)} articles selected.")  # Debug print (after selection)
    return selected

