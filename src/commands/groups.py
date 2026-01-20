import discord
import sqlite3
from traceback import print_exc
import db_helpers # just for testing, remove this later (bad bad programming practice bruh)
import database
from discord import app_commands
from services.timezone_onboarding import timezone_prompt
from utils.command_helpers import validate_role
from utils.getters import get_user_id, get_display_name, get_guild_id
from utils.time import get_utc_now_iso
# /src is the import root, so commands is a package and command_helpers is a module inside it

group = app_commands.Group(
    name="group",
    description="Day-One habit-group management commands"
)

@group.command(name="leave", description="Leave a habit group")
async def leave_group(interaction: discord.Interaction, name: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    display_name = get_display_name(interaction)
    group_name = name.strip().upper()
    guild_id = get_guild_id(interaction)
    
    group_row = database.db_get_group_by_name(guild_id, group_name)   
    if group_row is None:
        await interaction.response.send_message(f"**{group_name}** does not exist in this server.", ephemeral=True)
        return
    group_id = group_row["id"] # TODO (nevermind, still need a None check before accessing dict) make a generic getter for groups get_from_group(guild_id, group_id, property="id"), maybe make one for all tables

    user_id = get_user_id(interaction)
    # XXX
    # TODO think about what you want to do with checkins and streaks (just reset streaks) after a user leaves
    # for now just delete checkins and streaks
    try:
        deleted = database.db_remove_member(guild_id, group_id, user_id)
        if deleted == 0:
            await interaction.response.send_message(f"You are not a member in **{group_name}**. Please use `/join {group_name}` command to join.", ephemeral=True)
            return
        await interaction.response.send_message(f"{display_name} has left **{group_name}**!")
    except sqlite3.IntegrityError as e:
        print(f"DB IntegrityError while leaving group {group_name}.")
        print_exc()

@group.command(name="join", description="Join a new habit group")
async def join_group(interaction: discord.Interaction, name: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    group_name = name.strip().upper()
    guild_id = interaction.guild_id

    group_row = database.db_get_group_by_name(guild_id, group_name)    
    if group_row is None: # no group with this name exists in that guild/db
        await interaction.response.send_message(f"**{group_name}** does not exist in this server.", ephemeral=True)
        return
    group_id = group_row["id"]
    
    user_display_name = get_display_name(interaction)
    user_id = get_user_id(interaction)
    joined_at = get_utc_now_iso()
    created_at = joined_at
    
    try:
        if database.db_get_user(user_id) is None:
            database.db_add_user(user_id, created_at, timezone=None) # add user to the db
        
        database.db_create_member(guild_id, group_id, user_id, joined_at) # add user to the habit group
    except sqlite3.IntegrityError as e:
        print(f"DB IntegrityError while joining group **{group_name}**.")
        print_exc()
        
        await interaction.response.send_message(f"User: {user_id} already exists in **{group_name}**.", ephemeral=True)
        return
    else:
        await interaction.response.send_message(f"{user_display_name} just started Day One in **{group_name}**!", ephemeral=False)
        await timezone_prompt(interaction)

    #test
    row = db_helpers.fetchone(
        "SELECT id, guild_id, group_id, user_id, joined_at FROM group_memberships WHERE guild_id=? AND group_id=?",
        (guild_id, group_id)
    )
    user_row = db_helpers.fetchone(
        "SELECT user_id, timezone, created_at, want_tz_prompts FROM users WHERE user_id=?",
        (user_id,)
    )
    print("Inserted user:", dict(user_row) if user_row else None)


@group.command(name="create", description="Create a new habit group")
async def create_group(interaction: discord.Interaction, name: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    if validate_role(interaction, ["Admin", "Mod"]):
        group_name = name.strip().upper()
        guild_id = get_guild_id(interaction)
        created_by = get_user_id(interaction)
        created_at = get_utc_now_iso()
        try:
            database.db_add_user(user_id=created_by, created_at=created_at, timezone=None) # TODO implement INSERT OR IGNORE in db or update/insert function in db)
            database.db_create_group(guild_id, group_name, created_by, created_at)
        except sqlite3.IntegrityError as e:
            # ungraceful error for dev
            print(f"DB IntegrityError while creating habit group **{group_name}**.")
            print_exc()
            
            # graceful error for user
            await interaction.response.send_message(f"**{group_name}** already exists in this server. Duplicate names are not allowed (for now).", ephemeral=True)
            return

        # test
        row = db_helpers.fetchone(
            "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=? AND name=?",
            (guild_id, group_name),
        )
        print("Inserted row:", dict(row) if row else None)
        
    else:
        await interaction.response.send_message("You need Admin/Mod to create a group", ephemeral=True)
        
    await interaction.response.send_message(f"Day One for **{group_name}** has started!", ephemeral=False)