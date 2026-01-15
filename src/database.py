import db_helpers


def init():
    conn = db_helpers.get_db_connection()
    # cur = conn.cursor()
    with open(db_helpers.BASE_DIR / "src/schema.sql") as f:
        conn.executescript(f.read())
    
    print("Database initialized successfully!")
    conn.commit()
    conn.close()

def db_create_group(guild_id, group_name, created_by, created_at):
    db_helpers.execute(
        "INSERT INTO habit_groups (guild_id, name, created_by, created_at) VALUES (?,?,?,?)",
        (guild_id, group_name, created_by, created_at)
    )
    return True

def db_get_group_by_name(guild_id, name):
    return db_helpers.fetchone(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=? AND name=?",
        (guild_id, name)
    )

# TODO get group by Id (later)


# TODO list groups for a guild
def db_get_guild_groups(guild_id):
    return db_helpers.fetchall(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=?",
        (guild_id)
    )