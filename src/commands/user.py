# TODO /set_timezone user can call this after seeing the ephemeral prompt by timezone_prompt(interaction)
# TODO /disable_timezone -- to disable timezone prompts (default to UTC), calls database method
# TODO /enable_timezone  -- just make it for testing, dont really need it

import discord
from discord import app_commands
from services.timezone_onboarding import validate_timezone
from database import db_update_timezone, db_update_tz_prompts
from utils.getters import get_user_id

user_group = app_commands.Group(
    name="user",
    description="Day-One commands for user settings"
)

@user_group.command(name="set_timezone", description="User can set timezone")
async def set_timezone(interaction: discord.Interaction, timezone: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    if not validate_timezone(str):
        await interaction.response.send_message("Please provide a valid timezone. For example:\n- `/set_timezone America/Chicago`\n- `/set_timezone Asia/Kolkata`\n- `/set_timezone Europe/Istanbul`\n\nIf you\'re not sure what yours is, see:\n<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>", ephemeral=True)
        return
    # now timezone is in valid IANA format
    # update timezone in db
    # BUG ensure user exists in the database first (send graceful error if not)
    db_update_timezone(str)
    
@user_group.command(name="disable_timezone", description="Disable prompts asking for timezone.")
async def disable_timezone(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    db_update_tz_prompts(get_user_id(interaction), "FALSE")
    await interaction.response.send_message("Timezone related prompts disabled.", ephemeral=True)

# Realistically, this is useless. But might need it for testing.
@user_group.command(name="enable_timezone", description="Enable prompts asking for timezone.")
async def enable_timezone(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    db_update_tz_prompts(get_user_id(interaction), "TRUE")
    await interaction.response.send_message("Timezone related prompts enabled.", ephemeral=True)