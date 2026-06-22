import discord
from discord import app_commands
from services.timezone_onboarding import validate_timezone
import database
from utils.logger import get_logger
from utils.getters import get_user_id

logger = get_logger(__name__)

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
        logger.info(
            "Invalid timezone rejected: user_id=%s guild_id=%s timezone=%s",
            get_user_id(interaction),
            interaction.guild_id,
            timezone,
        )
        await interaction.response.send_message("Please provide a valid timezone. For example:\n- `/set_timezone America/Chicago`\n- `/set_timezone Asia/Kolkata`\n- `/set_timezone Europe/Istanbul`\n\nIf you\'re not sure what yours is, see:\n<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>", ephemeral=True)
        return

    user_id = get_user_id(interaction)

    await database.db_update_timezone(
        user_id=user_id,
        timezone=timezone,
    )

    logger.info(
        "User timezone updated: user_id=%s guild_id=%s timezone=%s",
        user_id,
        interaction.guild_id,
        timezone,
    )

    await interaction.response.send_message(
        f"Your timezone is now set to `{timezone}`.",
        ephemeral=True,
    )
# ============================================================================================


# ============================================================================================
@user_group.command(name="disable_timezone", description="Disable prompts asking for timezone.")
async def disable_timezone(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    user_id = get_user_id(interaction)

    await database.db_update_tz_prompts(user_id, False)

    logger.info(
        "Timezone prompts disabled: user_id=%s guild_id=%s",
        user_id,
        interaction.guild_id,
    )
    
    await interaction.response.send_message("Timezone related prompts disabled.", ephemeral=True)
# ============================================================================================


# ============================================================================================
@user_group.command(name="enable_timezone", description="Enable prompts asking for timezone.")
async def enable_timezone(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    user_id = get_user_id(interaction)

    await database.db_update_tz_prompts(user_id, True)

    logger.info(
        "Timezone prompts enabled: user_id=%s guild_id=%s",
        user_id,
        interaction.guild_id,
    )
    
    await interaction.response.send_message("Timezone related prompts enabled.", ephemeral=True)
# ============================================================================================
