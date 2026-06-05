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
async def seed_group(interaction: discord.Interaction, name: str, allowed_skip_days: int=0, join_me: bool=True):
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
# ============================================================================================


# ============================================================================================
@dev_group.command(name="set_today", description="Set the fake current date for dev testing.",)
async def set_today(interaction: discord.Interaction, day: str,):
    await interaction.response.defer(ephemeral=True)

    try:
        if not is_dev(interaction):
            await interaction.followup.send("Dev command only.", ephemeral=True)
            return

        if interaction.guild_id is None:
            await interaction.followup.send(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        result = await database.dev_set_today(
            guild_id=interaction.guild_id,
            local_day=day,
        )

        await interaction.followup.send(
            f"Fake today set to `{result['today']}`.",
            ephemeral=True,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        await interaction.followup.send(
            f"set_today failed:\n```py\n{type(e).__name__}: {e}\n```",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@dev_group.command(
    name="advance_days",
    description="Move the fake current date forward or backward.",
)
async def advance_days(
    interaction: discord.Interaction,
    days: int,
):
    await interaction.response.defer(ephemeral=True)

    try:
        if not is_dev(interaction):
            await interaction.followup.send("Dev command only.", ephemeral=True)
            return

        if interaction.guild_id is None:
            await interaction.followup.send(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        result = await database.dev_advance_days(
            guild_id=interaction.guild_id,
            days=days,
        )

        await interaction.followup.send(
            "\n".join(
                [
                    "Fake date advanced.",
                    "",
                    f"Old today: `{result['old_today']}`",
                    f"Days changed: `{result['days']}`",
                    f"New today: `{result['new_today']}`",
                ]
            ),
            ephemeral=True,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        await interaction.followup.send(
            f"advance_days failed:\n```py\n{type(e).__name__}: {e}\n```",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================

# ============================================================================================


# ============================================================================================

# ============================================================================================


# ============================================================================================

# ============================================================================================
