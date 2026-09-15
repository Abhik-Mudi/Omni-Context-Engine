import sqlite3
from pathlib import Path

# 1. Get absolute path to the 'backend' folder, then go up one level to the root
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Define the target path for the 'data' folder
DATA_DIR = BASE_DIR / "data"

# 3. Force create the folder if it doesn't exist (prevents the OperationalError)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 4. Define the exact path to the database file
DB_PATH = DATA_DIR / "omni.db"

def init_db():
    # connects to a local database file
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()

    # creates a timeline_events table to store the events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            payload TEXT NOT NULL
        )
    ''')

    con.commit()
    con.close()
    print("Omni db created")

if __name__=="__main__":
    init_db()