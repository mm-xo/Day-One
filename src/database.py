import sqlite3

def init():
    conn = sqlite3.connect("data/day_one.db")
    # cur = conn.cursor()
    with open("src/schema.sql") as f:
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
