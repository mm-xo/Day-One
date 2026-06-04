import discord
from discord import app_commands
from services.timezone_onboarding import validate_timezone
from database import db_update_timezone, db_update_tz_prompts
from utils.getters import get_user_id

user_group = app_commands.Group(
    name="user",
    description="Day-One commands for user settings"
)


# ============================================================================================
@user_group.command(name="set_timezone", description="User can set timezone")
async def set_timezone(interaction: discord.Interaction, timezone: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    if not validate_timezone(timezone):
        await interaction.response.send_message("Please provide a valid timezone. For example:\n- `/set_timezone America/Chicago`\n- `/set_timezone Asia/Kolkata`\n- `/set_timezone Europe/Istanbul`\n\nIf you\'re not sure what yours is, see:\n<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>", ephemeral=True)
        return

    await interaction.response.send_message(f"Your timezone is now set to `{timezone}`.")
    await db_update_timezone(timezone)
# ============================================================================================


# ============================================================================================
@user_group.command(name="disable_timezone", description="Disable prompts asking for timezone.")
async def disable_timezone(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    await db_update_tz_prompts(get_user_id(interaction), "FALSE")
    await interaction.response.send_message("Timezone related prompts disabled.", ephemeral=True)
# ============================================================================================


# ============================================================================================
@user_group.command(name="enable_timezone", description="Enable prompts asking for timezone.")
async def enable_timezone(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    await db_update_tz_prompts(get_user_id(interaction), "TRUE")
    await interaction.response.send_message("Timezone related prompts enabled.", ephemeral=True)
# ============================================================================================
