import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent # project root directory
DB_PATH = BASE_DIR / "data" / "day_one.db"

def get_db_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = get_db_connection()
    # cur = conn.cursor()
    with open(BASE_DIR / "src/schema.sql") as f:
        conn.executescript(f.read())
    
    print("Database initialized successfully!")
    conn.commit()
    conn.close()

# Learning

# cur.execute("""CREATE TABLE customers(
#         first_name text,
#         last_name text,
#         email text
#     )""")

# Insert a record

# cur.execute("INSERT INTO customers VALUES ('John', 'Elder', 'john@email.com')")
# cur.execute("INSERT INTO customers VALUES ('tip', 'mum', 'tip@email.com')")
# cur.execute("INSERT INTO customers VALUES ('Mary', 'brown', 'mary@email.com')")

# Insert many records into the table

# many_customers = [('Wes', 'Brown', 'Wes@email.com'),
#                 ('Steph', 'Kuewa', 'steph@email.com'),
#                 ('Dan', 'Danny', 'Dan@email.com')]

# cur.executemany("INSERT INTO customers VALUES (?,?,?)", many_customers)
