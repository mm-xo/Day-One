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

# TODO get group by Id (later)


# TODO list groups for a guild
def db_get_guild_groups(guild_id):
    return db_helpers.fetchall(
        "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=?;",
        (guild_id)
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


# ================================================================
# TIMEZONE CRUD
# ================================================================
# TODO db_get_user_timezone(user_id)
# TODO db_update_timezone(user_id, timezone)
# TODO db_update_tz_prompts(user_id, preference)
# these get called using slash commands

def db_get_user_timezone(user_id):
    user_row = db_helpers.fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?;",
        (user_id)
    )
    return user_row["timezone"]

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