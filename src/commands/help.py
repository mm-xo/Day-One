import discord
from discord import app_commands


@app_commands.command(
    name="help",
    description="Show all regular Day One commands."
)
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Day One Help",
        description="Commands regular users can use in this server.",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="/group list",
        value=(
            "List all habit groups available in this server.\n"
            "`/group list`"
        ),
        inline=False
    )

    embed.add_field(
        name="/group join",
        value=(
            "Join an existing habit group.\n"
            "`/group join name:<group_name>`\n"
            "Example: `/group join name:GYM`"
        ),
        inline=False
    )

    embed.add_field(
        name="/group leave",
        value=(
            "Leave a habit group you are currently in.\n"
            "`/group leave name:<group_name>`\n"
            "Example: `/group leave name:GYM`"
        ),
        inline=False
    )

    embed.add_field(
        name="/group checkin",
        value=(
            "Check in for today in one of your joined groups.\n"
            "`/group checkin group_name:<group_name> note:<optional_note>`\n"
            "Example: `/group checkin group_name:GYM note:Leg day done`"
        ),
        inline=False
    )

    embed.add_field(
        name="/group stats",
        value=(
            "Show your stats, or another member's stats, in a habit group.\n"
            "`/group stats group_name:<group_name> member:<optional_member>`\n"
            "Example: `/group stats group_name:GYM`"
        ),
        inline=False
    )

    embed.add_field(
        name="/group leaderboard",
        value=(
            "Show group progress and streak rankings.\n"
            "`/group leaderboard group_name:<group_name>`\n"
            "Example: `/group leaderboard group_name:GYM`"
        ),
        inline=False
    )

    embed.add_field(
        name="/group create",
        value=(
            "Create a new habit group. Requires Admin or Mod role.\n"
            "`/group create name:<group_name> allowed_skip_days:<days>`\n"
            "Example: `/group create name:GYM allowed_skip_days:1`"
        ),
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)