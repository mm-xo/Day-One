
PRAGMA foreign_keys = ON;

-- HABIT groups
CREATE TABLE IF NOT EXISTS habit_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (guild_id, name)
    -- UNIQUE (guild_id, name) means the PAIR cannot repeat in this table
);

-- Group members
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    joined_at TEXT NOT NULL,

    FOREIGN KEY (group_id) REFERENCES habit_groups(id) ON DELETE CASCADE,
    -- Every group_id in this table must refer to a real row in habit_groups,
    -- and if that group is deleted, automatically delete these rows too.
    UNIQUE (group_id, user_id) -- same user cannot join a group more than once
);

-- Check-ins
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    day TEXT NOT NULL,                  -- YYYY-MM-DD (user local)
    note TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (group_id) REFERENCES habit_groups(id) ON DELETE CASCADE,
    UNIQUE (group_id, user_id, day)
    -- To stop spams
);

-- Streaks
CREATE TABLE IF NOT EXISTS streaks (
    group_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    current INTEGER NOT NULL DEFAULT 0,
    best INTEGER NOT NULL DEFAULT 0,
    last_day TEXT,

    FOREIGN KEY (group_id) REFERENCES habit_groups(id) ON DELETE CASCADE,
    UNIQUE (group_id, user_id)
);