# TODO create dev commands, only to be used by people with certain roles
# commands like custom dates for checkin etc for manual testing
from config import DEV_USER_IDS, DEV_GUILD_ID
import discord
from discord import app_commands
import database
from utils.logger import get_logger

logger = get_logger(__name__)


dev_group = app_commands.Group(
    name="dev",
    description="Day-One commands for manual testing"
)

def is_dev(interaction: discord.Interaction):
    return (interaction.guild_id == DEV_GUILD_ID and interaction.user.id in DEV_USER_IDS)


# ============================================================================================
@dev_group.command(name="reset", description="Reset all test data in the dev guild.")
async def reset(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not is_dev(interaction):
        logger.warning(
            "Unauthorized /dev reset attempt: user_id=%s guild_id=%s",
            interaction.user.id,
            interaction.guild_id,
        )
        await interaction.followup.send("Dev command only.", ephemeral=True)
        return

    try:
        deleted_counts = await database.dev_reset_guild(interaction.guild_id)

        logger.warning(
            "/dev reset used: user_id=%s guild_id=%s deleted_counts=%s",
            interaction.user.id,
            interaction.guild_id,
            deleted_counts,
        )

        lines = ["Dev reset complete.", "", "Deleted rows:"]

        for table_name, count in deleted_counts.items():
            lines.append(f"- `{table_name}`: `{count}`")

        await interaction.followup.send("\n".join(lines), ephemeral=True)

    except Exception:
        logger.exception(
            "/dev reset failed: user_id=%s guild_id=%s",
            interaction.user.id,
            interaction.guild_id,
        )
        await interaction.followup.send(
            "Dev reset failed. The error has been logged.",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@dev_group.command(name="seed_group", description="Create a test habit group in the dev guild.")
async def seed_group(
    interaction: discord.Interaction,
    name: str,
    allowed_skip_days: int = 0,
    join_me: bool = True,
):
    await interaction.response.defer(ephemeral=True)

    if not is_dev(interaction):
        logger.warning(
            "Unauthorized /dev seed_group attempt: user_id=%s guild_id=%s name=%s",
            interaction.user.id,
            interaction.guild_id,
            name,
        )
        await interaction.followup.send("Dev command only.", ephemeral=True)
        return

    if interaction.guild_id is None:
        await interaction.followup.send(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    try:
        result = await database.dev_seed_group(
            guild_id=interaction.guild_id,
            group_name=name.upper(),
            created_by=interaction.user.id,
            allowed_skip_days=allowed_skip_days,
            join_creator=join_me,
        )

        logger.info(
            "/dev seed_group used: user_id=%s guild_id=%s group_name=%s group_id=%s allowed_skip_days=%s join_me=%s created_new=%s",
            interaction.user.id,
            interaction.guild_id,
            result["group_name"],
            result["group_id"],
            allowed_skip_days,
            join_me,
            result["created_new_group"],
        )

        created_text = "yes" if result["created_new_group"] else "no, reused existing group"
        joined_text = "yes" if result["joined_creator"] else "no"

        await interaction.followup.send(
            "\n".join(
                [
                    "Seed group ready.",
                    "",
                    f"Group: `{result['group_name']}`",
                    f"Group ID: `{result['group_id']}`",
                    f"Allowed skip days: `{result['allowed_skip_days']}`",
                    f"Created new group: `{created_text}`",
                    f"Added you as member: `{joined_text}`",
                ]
            ),
            ephemeral=True,
        )

    except Exception:
        logger.exception(
            "/dev seed_group failed: user_id=%s guild_id=%s name=%s allowed_skip_days=%s join_me=%s",
            interaction.user.id,
            interaction.guild_id,
            name,
            allowed_skip_days,
            join_me,
        )
        await interaction.followup.send(
            "Seed group failed. The error has been logged.",
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
        
        logger.info(
            "/dev set_today used: user_id=%s guild_id=%s day=%s",
            interaction.user.id,
            interaction.guild_id,
            result["today"],
        )

        await interaction.followup.send(
            f"Fake today set to `{result['today']}`.",
            ephemeral=True,
        )

    except Exception:
        logger.exception(
            "/dev set_today failed: user_id=%s guild_id=%s day=%s",
            interaction.user.id,
            interaction.guild_id,
            day,
        )
        await interaction.followup.send(
            "set_today failed. The error has been logged.",
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
        
        logger.info(
            "/dev advance_days used: user_id=%s guild_id=%s old_today=%s days=%s new_today=%s",
            interaction.user.id,
            interaction.guild_id,
            result["old_today"],
            result["days"],
            result["new_today"],
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

    except Exception:
        logger.exception(
            "/dev advance_days failed: user_id=%s guild_id=%s days=%s",
            interaction.user.id,
            interaction.guild_id,
            days,
        )
        await interaction.followup.send(
            "advance_days failed. The error has been logged.",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@dev_group.command(
    name="show_state",
    description="Show debug state for a user in a group.",
)
async def show_state(
    interaction: discord.Interaction,
    group_name: str,
    user: discord.Member | None = None,
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

        target_user = user or interaction.user

        result = await database.dev_show_state(
            guild_id=interaction.guild_id,
            group_name=group_name.upper(),
            user_id=target_user.id,
        )
        
        logger.info(
            "/dev show_state used: user_id=%s guild_id=%s group_name=%s target_user_id=%s found_group=%s",
            interaction.user.id,
            interaction.guild_id,
            group_name.upper(),
            target_user.id,
            result["found_group"],
        )

        if not result["found_group"]:
            await interaction.followup.send(
                f"Group `{group_name}` was not found.\nFake today: `{result['today']}`",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "\n".join(
                [
                    "Debug state:",
                    "",
                    f"Group: `{result['group_name']}`",
                    f"Group ID: `{result['group_id']}`",
                    f"Allowed skip days: `{result['allowed_skip_days']}`",
                    "",
                    f"User: {target_user.mention}",
                    f"User ID: `{result['user_id']}`",
                    f"Is member: `{result['is_member']}`",
                    "",
                    f"Fake today: `{result['today']}`",
                    f"Checked in today: `{result['has_checkin_today']}`",
                    f"Current streak: `{result['current_streak']}`",
                    f"Best streak: `{result['best_streak']}`",
                    f"Last check-in: `{result['last_checkin']}`",
                ]
            ),
            ephemeral=True,
        )

    except Exception:
        logger.exception(
            "/dev show_state failed: user_id=%s guild_id=%s group_name=%s target_user=%s",
            interaction.user.id,
            interaction.guild_id,
            group_name,
            user.id if user else interaction.user.id,
        )
        await interaction.followup.send(
            "show_state failed. The error has been logged.",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@dev_group.command(
    name="checkin_as",
    description="Simulate a check-in as another user.",
)
async def checkin_as(
    interaction: discord.Interaction,
    group_name: str,
    user: discord.Member,
    note: str | None = None,
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

        result = await database.dev_checkin_as(
            guild_id=interaction.guild_id,
            group_name=group_name.upper(),
            user_id=user.id,
            note=note,
        )

        if not result["success"]:
            if result["reason"] == "group_not_found":
                await interaction.followup.send(
                    f"Group `{group_name}` was not found.",
                    ephemeral=True,
                )
                return

            if result["reason"] == "already_checked_in":
                
                logger.info(
                    "/dev checkin_as duplicate blocked: actor_id=%s guild_id=%s target_user_id=%s group_name=%s local_day=%s",
                    interaction.user.id,
                    interaction.guild_id,
                    user.id,
                    result["group_name"],
                    result["local_day"],
                )
                
                await interaction.followup.send(
                    "\n".join(
                        [
                            "User already checked in today.",
                            "",
                            f"Group: `{result['group_name']}`",
                            f"User: {user.mention}",
                            f"Fake today: `{result['local_day']}`",
                            f"Current streak: `{result['current_streak']}`",
                            f"Best streak: `{result['best_streak']}`",
                            f"Last check-in: `{result['last_checkin']}`",
                        ]
                    ),
                    ephemeral=True,
                )
                return

        logger.info(
            "/dev checkin_as used: actor_id=%s guild_id=%s target_user_id=%s group_name=%s local_day=%s current=%s best=%s continued=%s joined_user=%s",
            interaction.user.id,
            interaction.guild_id,
            user.id,
            result["group_name"],
            result["local_day"],
            result["current_streak"],
            result["best_streak"],
            result["streak_continued"],
            result["joined_user"],
        )

        await interaction.followup.send(
            "\n".join(
                [
                    "Dev check-in complete.",
                    "",
                    f"Group: `{result['group_name']}`",
                    f"Group ID: `{result['group_id']}`",
                    f"User: {user.mention}",
                    f"Fake today: `{result['local_day']}`",
                    f"Auto-joined user: `{result['joined_user']}`",
                    "",
                    f"Current streak: `{result['current_streak']}`",
                    f"Best streak: `{result['best_streak']}`",
                    f"Streak continued: `{result['streak_continued']}`",
                ]
            ),
            ephemeral=True,
        )

    except Exception:
        logger.exception(
            "/dev checkin_as failed: actor_id=%s guild_id=%s target_user_id=%s group_name=%s",
            interaction.user.id,
            interaction.guild_id,
            user.id,
            group_name,
        )
        await interaction.followup.send(
            "checkin_as failed. The error has been logged.",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@dev_group.command(name="test_log", description="Test the logger system.")
async def test_log(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not is_dev(interaction):
        await interaction.followup.send("Dev command only.", ephemeral=True)
        return

    logger.debug("DEBUG test log")
    logger.info("INFO test log")
    logger.warning("WARNING test log")
    logger.error("ERROR test log")

    await interaction.followup.send(
        "Test logs sent. Check terminal, log file, and Discord log channel.",
        ephemeral=True,
    )
# ============================================================================================
