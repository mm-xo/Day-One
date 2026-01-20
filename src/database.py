import db_helpers
# TODO migrate to SQL alchemy later


def init():
    conn = db_helpers.get_db_connection()
    # cur = conn.cursor()
    with open(db_helpers.BASE_DIR / "src/schema.sql") as f:
        conn.executescript(f.read())
    
    print("Database initialized successfully!")
    conn.commit()
    conn.close()
    

# ================================================================
# HABIT GROUP CRUD
# ================================================================
def db_create_group(guild_id, group_name, created_by, created_at):
    db_helpers.execute(
        "INSERT INTO habit_groups (guild_id, name, created_by, created_at) VALUES (?,?,?,?);",
        (guild_id, group_name, created_by, created_at)
    )
    return True

def db_get_group_by_name(guild_id, name):
    return db_helpers.fetchone(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=? AND name=?;",
        (guild_id, name)
    )

# TODO get group by Id (later maybe)


# TODO list groups for a guild
def db_get_guild_groups(guild_id):
    return db_helpers.fetchall(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=?;",
        (guild_id,)
    )
    # TODO return member count with each group


# TODO delete group (row from habit_groups table)

# ================================================================


# ================================================================
# GROUP MEMBERSHIP CRUD
# ================================================================
def db_create_member(guild_id, group_id, user_id, joined_at):
    db_helpers.execute(
        "INSERT INTO group_memberships (guild_id, group_id, user_id, joined_at) VALUES (?,?,?,?);",
        (guild_id, group_id, user_id, joined_at)
    )
    return True

def db_remove_member(guild_id, group_id, user_id):
    cur = db_helpers.execute(
        "DELETE FROM group_memberships WHERE guild_id=? AND group_id=? AND user_id=?;",
        (guild_id, group_id, user_id)
    )
    return cur.rowcount

# ================================================================
# USERS CRUD
# ================================================================
def db_add_user(user_id, created_at, timezone=None): # Default timezone
    if timezone is None:
        db_helpers.execute(
            "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?,?);",
            (user_id, created_at)
        )
    else:
        pass # TODO

    return True

def db_get_user(user_id):
    return db_helpers.execute(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )


# ================================================================
# TIMEZONE CRUD
# ================================================================
def db_get_user_timezone(user_id):
    user_row = db_helpers.fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
    return user_row["timezone"] # BUG if user doesnt exists, this will throw an error

# TODO make generic getters for all tables. They take the necessary parameters,
# and a parameter equal to a property name in the table (e.g., "created_at", "guild_id", etc)

def db_get_tz_prompt(user_id):
    user_row = db_helpers.fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id,)
    )
    return user_row["want_tz_prompts"] # BUG if user doesnt exists, this will throw an error

def db_update_timezone(user_id, timezone="UTC"):
    db_helpers.execute(
        "UPDATE users SET timezone=? WHERE user_id=?;",
        (timezone, user_id)
    )
    return True

def db_update_tz_prompts(user_id, preference):
    db_helpers.execute(
        "UPDATE users SET want_tz_prompts=? WHERE user_id=?;",
        (preference, user_id)
    )