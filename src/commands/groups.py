import discord
import sqlite3
from traceback import print_exc
import database
from discord import app_commands
from services.timezone_onboarding import timezone_prompt
from utils.command_helpers import validate_role, is_command_in_server
from utils.getters import get_user_id, get_display_name, get_guild_id
from utils.time import get_utc_now_iso, get_local_today_iso
# /src is the import root, so commands is a package and command_helpers is a module inside it


group = app_commands.Group(
    name="group",
    description="Day-One habit-group management commands"
)


# ============================================================================================
@group.command(name="checkin", description="Log your habit in a joined group.")
async def checkin(interaction: discord.Interaction, group_name: str, note: str):
    
    if not await is_command_in_server(interaction):
        return
    
    group_name = group_name.strip().upper()
    guild_id = get_guild_id(interaction)
    user_id = get_user_id(interaction)
    display_name = get_display_name(interaction)
    
    group = await database.db_get_group_by_id_name(guild_id, group_name)
    
    if group is None:
        await interaction.response.send_message(f"**{group_name}** does not exist in this server.", ephemeral=True)
        return
    
    group_id = group["id"]
    allowed_skip_days = database.db_get_skip_days(guild_id, group_name)
    
    is_member = await database.db_is_user_member(guild_id=guild_id, group_id=group_id, user_id=user_id)
    
    if not is_member:
        await interaction.response.send_message(
            f"You are not a member of **{group_name}**. Join first with `/group join {group_name}`.",
            ephemeral=True
        )
        return
    
    user_tz = await database.db_get_user_timezone(user_id=user_id)
    
    checkin_date_local = get_local_today_iso(user_tz)
    
    checked_in_at_utc = get_utc_now_iso()
    
    already_checked_in = await database.db_has_checkin_today(guild_id, group_id, user_id, checkin_date_local)
    
    if already_checked_in:
        await interaction.response.send_message(f"You already checked in for **{group_name}** today.", ephemeral=True)
        return
    
    # TODO get note
    note = "this is a note"
    
    try:
        await database.db_create_checkin(guild_id, group_id, user_id, note, checkin_date_local, checked_in_at_utc)
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"You already checked in for **{group_name}** today.")
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
    except sqlite3.Error as e:
        print("DB Error occured while serving /list command.")
        print_exc()
# ============================================================================================


# ============================================================================================
@group.command(name="leave", description="Leave a habit group")
async def leave_group(interaction: discord.Interaction, name: str):

    if not await is_command_in_server(interaction):
        return
    
    display_name = get_display_name(interaction)
    group_name = name.strip().upper()
    guild_id = get_guild_id(interaction)
    
    group_row = await database.db_get_group_by_id_name(guild_id, group_name)
    if group_row is None:
        await interaction.response.send_message(f"**{group_name}** does not exist in this server.", ephemeral=True)
        return
    
    group_id = group_row["id"]

    user_id = get_user_id(interaction)

    try:
        deleted = await database.db_remove_member(guild_id, group_id, user_id)
        if deleted == 0:
            await interaction.response.send_message(f"You are not a member in **{group_name}**. Please use `/join {group_name}` command to join.", ephemeral=True)
            return
        else:
            await interaction.response.send_message(f"{display_name} has left **{group_name}**!")
    except sqlite3.IntegrityError as e:
        print(f"DB IntegrityError while leaving group {group_name}.")
        print_exc()
# ============================================================================================


# ============================================================================================
@group.command(name="join", description="Join a new habit group")
async def join_group(interaction: discord.Interaction, name: str):

    if not await is_command_in_server(interaction):
        return
    
    group_name = name.strip().upper()
    guild_id = interaction.guild_id

    group_row = await database.db_get_group_by_id_name(guild_id, group_name)
    if group_row is None:
        await interaction.response.send_message(f"**{group_name}** does not exist in this server.", ephemeral=True)
        return
    group_id = group_row["id"]
    
    user_display_name = get_display_name(interaction)
    user_id = get_user_id(interaction)
    joined_at = get_utc_now_iso()
    created_at = joined_at
    
    try:
        await database.db_add_user(user_id, created_at, timezone=None)
        await database.db_create_member(guild_id, group_id, user_id, joined_at)
    except sqlite3.IntegrityError as e:
        print(f"DB IntegrityError while joining group **{group_name}**.")
        print_exc()
        
        await interaction.response.send_message(f"You are already a member in **{group_name}**.", ephemeral=True)
        return
    else:
        await interaction.response.send_message(f"Welcome {user_display_name} to your Day One in **{group_name}**!", ephemeral=False)
        await timezone_prompt(interaction)

    #test
    row = await database.fetchone(
        "SELECT id, guild_id, group_id, user_id, joined_at FROM group_memberships WHERE guild_id=? AND group_id=?",
        (guild_id, group_id)
    )
    user_row = await database.fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?",
        (user_id,)
    )
    print("Inserted user:", dict(user_row) if user_row else None)
# ============================================================================================


# ============================================================================================
@group.command(name="create", description="Create a new habit group")
async def create_group(interaction: discord.Interaction, name: str, allowed_skip_days: int = 0):

    if not await is_command_in_server(interaction):
        return
    
    if validate_role(interaction, ["Admin", "Mod"]):
        group_name = name.strip().upper()
        guild_id = get_guild_id(interaction)
        created_by = get_user_id(interaction)
        created_at = get_utc_now_iso()
        try:
            await database.db_add_user(user_id=created_by, created_at=created_at, timezone=None) # TODO implement INSERT OR IGNORE in db or update/insert function in db)
            await database.db_create_group(guild_id, group_name, created_by, created_at, allowed_skip_days)
            await interaction.response.send_message(f"Day One for group **{group_name}** has started!\nUser are allowed to skip check-ins for **{allowed_skip_days}** days without breaking their streak.", ephemeral=False)
        except sqlite3.IntegrityError as e:
            # ungraceful error for dev
            print(f"DB IntegrityError while creating habit group **{group_name}**.")
            print_exc()
            
            # graceful error for user
            await interaction.response.send_message(f"**{group_name}** already exists in this server. Duplicate names are not allowed (for now).", ephemeral=True)
            return

        # test
        row = await database.fetchone(
            "SELECT id, guild_id, name, created_by, created_at, allowed_skip_days FROM habit_groups WHERE guild_id=? AND name=?",
            (guild_id, group_name),
        )
        print("Inserted row:", dict(row) if row else None)
        
    else:
        await interaction.response.send_message("You need Admin/Mod to create a group", ephemeral=True)
# ============================================================================================
