import os
from dotenv import load_dotenv

load_dotenv()

SYNC_GLOBAL_COMMANDS = os.getenv("SYNC_GLOBAL_COMMANDS", "false").lower() == "true"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0"))
ADMIN_ROLES = os.getenv("ADMIN_ROLES")

DEV_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("DEV_USER_IDS", "").split(",")
    if user_id.strip()
}

DISCORD_LOG_CHANNEL_ID = int(os.getenv("DISCORD_LOG_CHANNEL_ID", "0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in .env")