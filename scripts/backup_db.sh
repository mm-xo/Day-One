#!/usr/bin/env bash

set -euo pipefail

APP_DIR="$HOME/Day-One"
DB_PATH="$APP_DIR/data/day_one.db"
BACKUP_DIR="$APP_DIR/backups"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"

mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_PATH" ]; then
	echo "Database not found at $DB_PATH"
	exit 1
fi

BACKUP_FILE="$BACKUP_DIR/day_one_$TIMESTAMP.db"

sqlite3 "$DB_PATH" ".backup $BACKUP_FILE"

gzip "$BACKUP_FILE"

# keep only backups from the last 14 days
find "$BACKUP_DIR" -name "day_one_*.db.gz" -type f -mtime +14 -delete

echo "Backup created: $BACKUP_FILE.gz"
