import discord
from discord import app_commands

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
    
    
    
    await interaction.response.send_message(f"Day-One for habit group **{name}** has started!")