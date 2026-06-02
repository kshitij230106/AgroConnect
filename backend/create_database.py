import sqlite3

conn = sqlite3.connect("data/agroconnect.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()

conn.close()

print("Farmers table created successfully")