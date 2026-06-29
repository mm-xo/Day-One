import discord
import sqlite3
import database
import config
from discord import app_commands
from services.timezone_onboarding import timezone_prompt
from services.group_logic import is_valid_allowed_skip_days, normalize_group_name, is_valid_group_name
from utils.command_helpers import validate_role, build_group_stats_embed, is_command_in_server, get_leaderboard_display_names, LeaderboardPaginationView
from utils.getters import get_user_id, get_display_name, get_guild_id
from utils.time import get_utc_now_iso, get_local_today_iso
from utils.logger import get_logger
# /src is the import root, so commands is a package and command_helpers is a module inside it

# TODO make it cleaner: separate business logic into services/ directory and just handle discord related stuff in commands
# Also make file(s) for constants

logger = get_logger(__name__)

group = app_commands.Group(
    name="group",
    description="Day-One habit-group management commands"
)


# ============================================================================================
async def get_group_or_respond(interaction: discord.Interaction, group_name: str):
    guild_id = get_guild_id(interaction)
    
    group_row = await database.db_get_group_by_id_name(guild_id, group_name)
    
    if group_row is None:
        await interaction.response.send_message(
            f"**{group_name}** does not exist in this server.",
            ephemeral=True
        )
        return None
    
    return group_row
# ============================================================================================


# ============================================================================================
async def require_group_member(interaction: discord.Interaction, guild_id: int, group_id: int, group_name: str, user_id: int) -> bool:
    
    is_member = await database.db_is_user_member(guild_id, group_id, user_id)
    
    if not is_member:
        await interaction.response.send_message(
            f"You are not a member of **{group_name}**. Join first with `/group join {group_name}`.",
            ephemeral=True
        )
        return False
    
    return True
# ============================================================================================


# ============================================================================================
@group.command(name="checkin", description="Log your habit in a joined group.")
async def checkin(interaction: discord.Interaction, group_name: str, note: str = ""):
    
    if not await is_command_in_server(interaction):
        return
    
    group_name = normalize_group_name(group_name)
    guild_id = get_guild_id(interaction)
    user_id = get_user_id(interaction)
    display_name = get_display_name(interaction)
    
    group_row = await get_group_or_respond(interaction, group_name)
    
    if group_row is None:
        return
    
    group_id = group_row["id"]
    allowed_skip_days = await database.db_get_skip_days(guild_id, group_name)
    
    if not await require_group_member(interaction, guild_id, group_id, group_name, user_id):
        return
    
    user_tz = await database.db_get_user_timezone(user_id=user_id)
    
    if guild_id == int(config.DEV_GUILD_ID):
        checkin_date_local = database.dev_get_today(guild_id)
    else:
        checkin_date_local = get_local_today_iso(user_tz)
    
    checked_in_at_utc = get_utc_now_iso()
    
    already_checked_in = await database.db_has_checkin_today(guild_id, group_id, user_id, checkin_date_local)
    
    if already_checked_in:
        logger.info(
            "Duplicate check-in blocked: user_id=%s guild_id=%s group_id=%s group_name=%s local_day=%s",
            user_id,
            guild_id,
            group_id,
            group_name,
            checkin_date_local,
        )
        await interaction.response.send_message(
            f"You already checked in for **{group_name}** today.",
            ephemeral=True,
        )
        return
    
    try:
        await database.db_create_checkin(guild_id, group_id, user_id, note, checkin_date_local, checked_in_at_utc)
        
    except sqlite3.IntegrityError:
        logger.info(
            "Duplicate check-in blocked by DB constraint: user_id=%s guild_id=%s group_id=%s group_name=%s local_day=%s",
            user_id,
            guild_id,
            group_id,
            group_name,
            checkin_date_local,
        )
        await interaction.response.send_message(
            f"You already checked in for **{group_name}** today.",
            ephemeral=True,
        )
        return
    
    current, best, streak_continued = await database.db_update_streak_after_checkin(guild_id, group_id, user_id, checkin_date_local, allowed_skip_days)
    
    if streak_continued:
        message = (
            f"{display_name} checked in for **{group_name}**!\n"
            f"Current streak: **{current}**\n"
            f"Longest streak: **{best}**"
        )
    else:
        message = (
            f"{display_name} checked in for **{group_name}**\n"
            f"Your streak restarted because you skipped more than **{allowed_skip_days} consecutive day(s)**\n"
            f"Current streak: **{current}**\n"
            f"Longest streak: **{best}**"
        )
        
    logger.info(
        "Check-in created: user_id=%s guild_id=%s group_id=%s group_name=%s local_day=%s current=%s best=%s continued=%s",
        user_id,
        guild_id,
        group_id,
        group_name,
        checkin_date_local,
        current,
        best,
        streak_continued,
    )
    
    await interaction.response.send_message(message)
# ============================================================================================


# ============================================================================================
@group.command(name="list", description="List all groups in the server.")
async def list_groups(interaction: discord.Interaction):
    
    if not await is_command_in_server(interaction):
        return
    
    try:
        group_rows = await database.db_get_guild_groups(guild_id = get_guild_id(interaction))
        group_rows = list(group_rows)
        if not group_rows:
            await interaction.response.send_message("There are no habit groups in this server right now. Only users with Admin/Mod role can create a habit group.", ephemeral=True)
            return
        available_groups = "Below are the groups available in this server:\n"
        for group_row in group_rows:
            available_groups += f"- {group_row["name"]}\n"
        available_groups += "\nPlease use `/group join [name]` to join."
        await interaction.response.send_message(available_groups, ephemeral=True)
        
    except sqlite3.Error:
        logger.exception(
            "Database error while listing groups: guild_id=%s user_id=%s",
            get_guild_id(interaction),
            get_user_id(interaction),
        )
        await interaction.response.send_message(
            "Could not list groups right now. The error has been logged.",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@group.command(name="leave", description="Leave a habit group")
async def leave_group(interaction: discord.Interaction, name: str):

    if not await is_command_in_server(interaction):
        return
    
    display_name = get_display_name(interaction)
    group_name = name.strip().upper()
    guild_id = get_guild_id(interaction)
    
    group_row = await get_group_or_respond(interaction, group_name)
    
    if group_row is None:
        return
    
    group_id = group_row["id"]

    user_id = get_user_id(interaction)

    try:
        deleted = await database.db_remove_member(guild_id, group_id, user_id)
        if deleted == 0:
            await interaction.response.send_message(f"You are not a member in **{group_name}**. Please use `/join {group_name}` command to join.", ephemeral=True)
            return
        else:
            logger.info(
                "User left group: user_id=%s guild_id=%s group_id=%s group_name=%s",
                user_id,
                guild_id,
                group_id,
                group_name,
            )
            await interaction.response.send_message(f"{display_name} has left **{group_name}**!")
    
    except sqlite3.IntegrityError:
        logger.exception(
            "Database integrity error while leaving group: user_id=%s guild_id=%s group_id=%s group_name=%s",
            user_id,
            guild_id,
            group_id,
            group_name,
        )
        await interaction.response.send_message(
            "Could not leave the group right now. The error has been logged.",
            ephemeral=True,
        )
# ============================================================================================


# ============================================================================================
@group.command(name="join", description="Join a new habit group")
async def join_group(interaction: discord.Interaction, name: str):

    if not await is_command_in_server(interaction):
        return
    
    group_name = name.strip().upper()
    guild_id = interaction.guild_id

    group_row = await get_group_or_respond(interaction, group_name)
    
    if group_row is None:
        return

    group_id = group_row["id"]
    
    user_display_name = get_display_name(interaction)
    user_id = get_user_id(interaction)
    joined_at = get_utc_now_iso()
    created_at = joined_at
    
    try:
        await database.db_add_user(user_id, created_at, timezone=None)
        await database.db_create_member(guild_id, group_id, user_id, joined_at)
        
    except sqlite3.IntegrityError:
        logger.info(
            "Join blocked because user is already member or membership constraint failed: user_id=%s guild_id=%s group_id=%s group_name=%s",
            user_id,
            guild_id,
            group_id,
            group_name,
        )

        await interaction.response.send_message(
            f"You are already a member in **{group_name}**.",
            ephemeral=True,
        )
        return
    
    else:
        logger.info(
            "User joined group: user_id=%s guild_id=%s group_id=%s group_name=%s",
            user_id,
            guild_id,
            group_id,
            group_name,
        )
        await interaction.response.send_message(f"Welcome {user_display_name}, to your Day One in **{group_name}**!", ephemeral=False)
        await timezone_prompt(interaction)
# ============================================================================================


# ============================================================================================
@group.command(name="create", description="Create a new habit group")
async def create_group(interaction: discord.Interaction, name: str, allowed_skip_days: int = 0):

    if not await is_command_in_server(interaction):
        return
    
    if not validate_role(interaction, config.ADMIN_ROLES):
        await interaction.response.send_message(
            "You need Admin/Mod role to create a group.",
            ephemeral=True
        )
        return
    
    if not is_valid_group_name(name):
        await interaction.response.send_message(
            "Group names must be 2–16 characters and can only use letters, numbers, spaces, hyphens, or underscores.",
            ephemeral=True
        )
        return

    group_name = normalize_group_name(name)
    guild_id = get_guild_id(interaction)
    created_by = get_user_id(interaction)
    created_at = get_utc_now_iso()
    
    if not is_valid_allowed_skip_days(allowed_skip_days):
        await interaction.response.send_message(
            "Allowed skip days must be between 0 and 7.",
            ephemeral=True
        )
        return
    
    try:
        await database.db_add_user(user_id=created_by, created_at=created_at, timezone=None)
        await database.db_create_group(guild_id, group_name, created_by, created_at, allowed_skip_days)
        
    except sqlite3.IntegrityError:
        logger.info(
            "Create group blocked because group already exists or constraint failed: user_id=%s guild_id=%s group_name=%s",
            created_by,
            guild_id,
            group_name,
        )

        await interaction.response.send_message(
            f"**{group_name}** already exists in this server. Duplicate names are not allowed.",
            ephemeral=True,
        )
        return
    
    logger.info(
        "Group created: user_id=%s guild_id=%s group_name=%s allowed_skip_days=%s",
        created_by,
        guild_id,
        group_name,
        allowed_skip_days,
    )
    
    await interaction.response.send_message(
        f"Day One for group **{group_name}** has started!\n"
        f"Users are allowed to skip check-ins for **{allowed_skip_days}** days without breaking their streak.",
        ephemeral=False
    )
# ============================================================================================


# ============================================================================================
@group.command(
    name="delete",
    description="Delete a habit group."
)
async def delete(interaction: discord.Interaction, group_name: str, confirm: bool = False):

    if not await is_command_in_server(interaction):
        return

    if not validate_role(interaction, config.ADMIN_ROLES):
        await interaction.response.send_message(
            "You need an Admin/Mod role to delete a group.",
            ephemeral=True
        )
        return
    
    group_name = group_name.upper()

    if not is_valid_group_name(group_name):
        await interaction.response.send_message(
            "Invalid group name.",
            ephemeral=True
        )
        return

    if not confirm:
        await interaction.response.send_message(
            f"Deleting `{group_name}` will remove the group and its related check-ins, memberships, and streak data.\n\n"
            f"Run the command again with `confirm: True` to delete it.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    deleted_counts = await database.db_delete_group(
        guild_id=interaction.guild_id,
        group_name=group_name
    )

    if deleted_counts is None:
        await interaction.followup.send(
            f"No group named `{group_name}` was found.",
            ephemeral=True
        )
        return

    lines = [
        f"Deleted group `{group_name}`.",
        "",
        "Deleted rows:"
    ]

    for table_name, count in deleted_counts.items():
        lines.append(f"- `{table_name}`: `{count}`")

    await interaction.followup.send(
        "\n".join(lines),
        ephemeral=True
    )
# ============================================================================================


# ============================================================================================
@group.command(
    name="leaderboard",
    description="Show group progress and streak rankings."
)
async def leaderboard(interaction: discord.Interaction, group_name: str):
    await interaction.response.defer()

    guild_id = interaction.guild_id
    guild = interaction.guild
    group_name=group_name.upper()

    if guild_id is None or guild is None:
        await interaction.followup.send(
            "This command can only be used inside a server.",
            ephemeral=True,
        )
        return

    group = await database.db_get_group_by_id_name(
        guild_id=guild_id,
        name=group_name,
    )

    if group is None:
        await interaction.followup.send(
            f"I could not find a group named `{group_name}`.",
            ephemeral=True,
        )
        return

    rows = await database.db_get_group_leaderboard(
        guild_id=guild_id,
        group_id=group["id"],
    )

    display_names = await get_leaderboard_display_names(
        guild=guild,
        rows=rows,
    )

    view = LeaderboardPaginationView(
        group_name=group["name"],
        rows=rows,
        display_names=display_names,
        page_size=5,
    )

    if view.total_pages > 1:
        await interaction.followup.send(
            embed=view.make_embed(),
            view=view,
            allowed_mentions=discord.AllowedMentions.none(),
        )
    else:
        await interaction.followup.send(
            embed=view.make_embed(),
            allowed_mentions=discord.AllowedMentions.none(),
        )
# ============================================================================================


# ============================================================================================
@group.command(
    name="stats",
    description="Show your stats in a habit group."
)
async def stats(
    interaction: discord.Interaction,
    group_name: str,
    member: discord.Member | None = None,
):
    await interaction.response.defer()

    guild_id = interaction.guild_id
    group_name=group_name.upper()

    if guild_id is None:
        await interaction.followup.send(
            "This command can only be used inside a server.",
            ephemeral=True,
        )
        return

    group = await database.db_get_group_by_id_name(
        guild_id=guild_id,
        name=group_name,
    )

    if group is None:
        await interaction.followup.send(
            f"I could not find a group named `{group_name}`.",
            ephemeral=True,
        )
        return

    target = member or interaction.user
    target_user_id = target.id

    display_name = getattr(target, "display_name", target.name)

    stats_row = await database.db_get_group_member_stats(
        guild_id=guild_id,
        group_id=group["id"],
        user_id=target_user_id,
    )

    if stats_row is None:
        if target_user_id == interaction.user.id:
            message = f"You are not a member of `{group['name']}`."
        else:
            message = f"`{display_name}` is not a member of `{group['name']}`."

        await interaction.followup.send(
            message,
            ephemeral=True,
        )
        return

    embed = build_group_stats_embed(
        group_name=group["name"],
        display_name=display_name,
        stats_row=stats_row,
    )

    await interaction.followup.send(
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none(),
    )
# ============================================================================================
