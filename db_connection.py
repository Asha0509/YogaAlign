import sqlite3
import os

def get_db_connection():
    db_path = os.path.abspath('my_database.db')  # This will show exact path
    print("🔎 DB Path Used:", db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
