# TODO create dev commands, only to be used by people with certain roles
# commands like custom dates for checkin etc for manual testing
from config import DEV_USER_IDS, DEV_GUILD_ID, ADMIN_ROLES
import discord
from discord import app_commands
import database
from utils.command_helpers import is_command_in_server


dev_group = app_commands.Group(
    name="dev",
    description="Day-One commands for manual testing"
)

def is_dev(interaction):
    return (interaction.guild_id == DEV_GUILD_ID and interaction.user.id in DEV_USER_IDS)


# ============================================================================================
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
# ============================================================================================


# ============================================================================================
@dev_group.command(name="seed_group", description="Create a test habit group in the dev guild.")
async def seed_group(interaction, name: str, allowed_skip_days: int=0, join_me: bool=True):
    if not is_dev(interaction):
        await interaction.response.send_message("Dev command only.", ephemeral=True)
        return
    
    if not await is_command_in_server(interaction):
        await interaction.response.send_message("This command can only be used in a server", ephemeral=True)
        return
    
    result = await database.dev_seed_group(
        guild_id=interaction.guild_id,
        group_name=name,
        created_by=interaction.user.id,
        allowed_skip_days=allowed_skip_days,
        join_creator=join_me
    )
    
    created_text = "yes" if result["created_new_group"] else "no, reused existing group"
    joined_text = "yes" if result["joined_creator"] else "no"
    
    await interaction.response.defer(ephemeral=True)
    
    await interaction.followup.send(
        "\n".join(
            [
                "Seed group ready.",
                "",
                f"Group: `{result['group_name']}`",
                f"Group ID: `{result["group_id"]}`",
                f"Allowed skip days: `{result['allowed_skip_days']}`",
                f"Created new group: `{created_text}`",
                f"Added you as member: `{joined_text}`",
            ]
        ),
        ephemeral=True,
    )