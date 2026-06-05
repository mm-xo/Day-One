# TODO create dev commands, only to be used by people with certain roles
# commands like custom dates for checkin etc for manual testing
from config import DEV_USER_IDS, DEV_GUILD_ID, ADMIN_ROLES
import discord
from discord import app_commands
import database


dev_group = app_commands.Group(
    name="dev",
    description="Day-One commands for manual testing"
)

def is_dev(interaction):
    return (interaction.guild.id == DEV_GUILD_ID and interaction.user.id in DEV_USER_IDS)


@dev_group.command(name="reset", description="Reset all test data in the dev guild.")
async def reset(interaction: discord.Interaction):
    
    if not is_dev(interaction):
        await interaction.response.send_message("Dev command only.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    deleted_counts = await database.dev_reset_guild(interaction.guild_id)
    
    lines = ["Dev reset complete.", "", "Deleted rows:"]
    # await interaction.response.send_message("RESET COMPLETE")
    
    for table_name, count in deleted_counts.items():
        lines.append(f"- `{table_name}`: `{count}`")
        
    await interaction.followup.send("\n".join(lines), ephemeral=True)
