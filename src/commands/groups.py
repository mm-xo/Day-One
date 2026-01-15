import discord
import sqlite3
from traceback import print_exc
import db_helpers
import database
from discord import app_commands
from commands.command_helpers import validate_role, get_utc_now_iso
# /src is the import root, so commands is a package and command_helpers is a module inside it

group = app_commands.Group(
    name="group",
    description="Day-One habit-group management commands"
)

@group.command(name="join", description="Join a new habit group")
async def join_group(interaction: discord.Interaction, name: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    member = interaction.user # if someone uses this command in a guild, they are sure to be a member of the guild
    user_display_name = member.display_name
    group_name = name.strip().upper()
    # need guild_id, group_id, user_id, and joined_at utc time (for now)
    guild_id = interaction.guild_id
    group_id = database.db_get_group_by_name(guild_id, group_name)["id"]
    user_id = member.id
    joined_at = get_utc_now_iso() # TODO maybe time it after the code for inserting user into the group table is successful
    
    try:
        database.db_create_member(guild_id, group_id, user_id, joined_at)
    except sqlite3.IntegrityError as e:
        print(f"DB IntegrityError while joining group **{group_name}**.")
        print_exc()
        
        await interaction.response.send_message(f"User: {user_id} already exists in **{group_name}**.", ephemeral=True)
        return
    else:
        await interaction.response.send_message(f"{user_display_name} just started Day One in **{group_name}**", ephemeral=False)

    #test
    row = db_helpers.fetchone(
        "SELECT id, guild_id, group_id, user_id, joined_at FROM group_members WHERE guild_id=? AND group_id=?",
        (guild_id, group_id)
    )
    print("Inserted member:", dict(row) if row else None)


@group.command(name="create", description="Create a new habit group")
async def create_group(interaction: discord.Interaction, name: str):
    # TODO code functionality for group creation.
    # need to check the role of the user that invokes this command.
    # only users with "Mod" or "Admin" can create a group.
    # Think of ways to generalize it for other servers.
    
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return
    
    # FLOW: 1> validate authority of the user creating the group, continue only if valid
    # 2> take the group name, guild_id, created_id, and created_at time (in UTC for now)
    # insert group to db
    # member = interaction.guild.get_member(interaction.user.id) # users are global, members are guild specific    
    
    member = interaction.user
    if validate_role(member, ["Admin", "Mod"]):
        group_name = name.strip().upper()
        guild_id = interaction.guild_id
        created_by = interaction.user.id
        created_at = get_utc_now_iso()
        try:
            database.db_create_group(guild_id, group_name, created_by, created_at)
        except sqlite3.IntegrityError as e:
            # ungraceful error for dev
            print(f"DB IntegrityError while creating habit group **{group_name}**.")
            print_exc()
            
            # graceful error for user
            await interaction.response.send_message(f"A group with name {group_name} already exists in this server.", ephemeral=True)
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
