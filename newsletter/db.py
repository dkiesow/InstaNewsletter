import sqlite3

def ensure_model_table_and_get_device(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Model (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute("SELECT value FROM Model WHERE key = 'cpu_model'")
    row = c.fetchone()
    device = None
    if row:
        try:
            device = int(row[0])
            print(f"Loaded device from Model table: {device}")
        except Exception:
            device = row[0]
            print(f"Loaded device from Model table: {device}")
    conn.close()
    return device

def ensure_models_table_and_get_device(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Models (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute("SELECT value FROM Models WHERE key = 'cpu_model'")
    row = c.fetchone()
    device = None
    if row:
        try:
            device = int(row[0])
            print(f"Loaded device from Models table: {device}")
        except Exception:
            device = row[0]
            print(f"Loaded device from Models table: {device}")
    conn.close()
    return device

def save_device_to_model_table(db_path, device):
    conn = sqlite3.connect(db_path)
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

def save_device_to_models_table(db_path, device):
    conn = sqlite3.connect(db_path)
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

def get_existing_urls(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Ensure stories table exists with all columns
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_name TEXT,
        headline TEXT,
        url TEXT,
        author TEXT,
        publication_date TEXT,
        summary TEXT,
        source TEXT
    )''')
    conn.commit()
    conn.close()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT url FROM stories")
    existing_urls = set(row[0] for row in c.fetchall())
    conn.close()
    return existing_urls

def ensure_stories_table_has_source_column(conn):
    c = conn.cursor()
    c.execute("PRAGMA table_info(stories)")
    columns = [row[1] for row in c.fetchall()]
    if "source" not in columns:
        c.execute("ALTER TABLE stories ADD COLUMN source TEXT")
        conn.commit()

def save_to_db(db_path, records):
    print(f"Saving {len(records)} records to the database...")  # Debug print
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Ensure stories table exists with all columns
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_name TEXT,
        headline TEXT,
        url TEXT,
        author TEXT,
        publication_date TEXT,
        summary TEXT,
        source TEXT
    )''')
    ensure_stories_table_has_source_column(conn)
    c.execute("SELECT url FROM stories")
    existing_urls = set(row[0] for row in c.fetchall())
    for rec in records:
        db_headline = rec["headline"].replace('\n', ' ').replace('\r', ' ')
        if rec["url"] in existing_urls:
            continue
        c.execute('''INSERT INTO stories (publication_name, headline, url, author, publication_date, summary, source)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (
                      rec.get("publication_name", ""),
                      db_headline,
                      rec["url"],
                      rec["author"],
                      rec["publication_date"],
                      rec["summary"],
                      rec.get("source", rec.get("publication_name", "")),
                  ))
    conn.commit()
    conn.close()
    print("Records saved to database.")  # Debug print
