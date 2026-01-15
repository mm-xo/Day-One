import discord
import db_helpers
from discord import app_commands
from commands.command_helpers import validate_role, get_utc_now_iso
# /src is the import root, so commands is a package and command_helpers is a module inside it

group = app_commands.Group(
    name="group",
    description="Day-One habit-group management commands"
)

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
        group_name = name
        guild_id = interaction.guild_id
        created_by = interaction.user.id
        created_at = get_utc_now_iso()
        
        db_helpers.execute(
            "INSERT INTO habit_groups (guild_id, name, created_by, created_at) VALUES (?,?,?,?)",
            (guild_id, group_name, created_by, created_at)
        )
        # test
        row = db_helpers.fetchone(
            "SELECT id, guild_id, name, created_by, created_at FROM habit_groups WHERE guild_id=? AND name=?",
            (guild_id, name),
        )
    
        print("Inserted row:", dict(row) if row else None)
        
    else:
        interaction.response.send_message("You need Admin/Mod to create a group", ephemeral=True)
        
    await interaction.response.send_message(f"Day-One for **{name}** has started!")
