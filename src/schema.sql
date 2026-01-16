
PRAGMA foreign_keys = ON;

-- HABIT groups
CREATE TABLE IF NOT EXISTS habit_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_by INTEGER NOT NULL,    -- user id of creator
    created_at TEXT NOT NULL,

    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE RESTRICT,
    UNIQUE (guild_id, name)
    -- UNIQUE (guild_id, name) means the PAIR cannot repeat in this table
);

-- Group memberships
CREATE TABLE IF NOT EXISTS group_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TEXT NOT NULL,
    left_at TEXT,

    FOREIGN KEY (group_id) REFERENCES habit_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    -- Every group_id in this table must refer to a real row in habit_groups,
    -- and if that group is deleted, automatically delete these rows too.
    -- (improved with rejoin functionality below) -- UNIQUE (group_id, user_id) -- same user cannot join a group more than once
);

-- makes sure a user has atmost one active membership per group (allows rejoins)
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_membership
ON group_memberships(group_id, user_id)
WHERE left_at IS NULL;

-- Check-ins
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    local_day TEXT NOT NULL,                  -- YYYY-MM-DD (user local timezone)
    note TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (group_id) REFERENCES habit_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (group_id, user_id, local_day)
    -- To stop spams
);

-- Streaks
CREATE TABLE IF NOT EXISTS streaks (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    current INTEGER NOT NULL DEFAULT 0,
    best INTEGER NOT NULL DEFAULT 0,
    last_local_day TEXT,

    FOREIGN KEY (group_id) REFERENCES habit_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (group_id, user_id)
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,   -- Discord snowflake
    timezone TEXT NOT NULL DEFAULT 'UTC',                -- e.g. "America/Winnipeg"
    created_at TEXT NOT NULL
);
