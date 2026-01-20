from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from utils.getters import get_user_id, get_timezone
from database import db_get_tz_prompt

# TODO timezone_prompt(interaction) 
# TODO validate_timestone(tz_str) # hahaha


async def timezone_prompt(interaction): # looks up user timezone, if missing (default) > send ephemeral follow-up with reason, instructions, and link
    user_id = get_user_id(interaction)
    current_tz = get_timezone(user_id)
    message = f"Set your timezone to ensure future streaks are tracked correctly and reset at your local midnight.\nYour current timezone in our database is **{current_tz}**.\n\nPlease use `/set_timezone [timezone]` command and choose your timezone. For example:\n- `/set_timezone America/Chicago`\n- `/set_timezone Asia/Kolkata`\n- `/set_timezone Europe/Istanbul`\n\nIf you\'re not sure what yours is, see:\n<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>\n\nThis only needs to be done once, and you can update it later.\n\nIf you\'d like to stop receiving timezone prompts, use `/disable_timezone`.\nNote: if no timezone is set, the default will be **UTC**."
    
    if db_get_tz_prompt(user_id) == "TRUE" and current_tz == "UTC": # user has default timezone, prompt them to update
        await interaction.followup.send(message, ephemeral=True)

def validate_timezone(tz_str): # checks whether the string the user typed is a valid IANA timezone
    try:
        ZoneInfo(tz_str)
        return True
    except ZoneInfoNotFoundError as e:
        return False

