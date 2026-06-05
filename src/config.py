import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = int(os.getenv("DEV_GUILD_ID", "0"))
ADMIN_ROLES = os.getenv("ADMIN_ROLES")

DEV_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv("DEV_USER_IDS", "").split(",")
    if user_id.strip()
}

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in .env")