import discord
from discord.ext import commands
import config
import database
from commands.groups import group as groups_command_group
from commands.user_settings import settings_group

intents = discord.Intents.default()

class HabitBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)

    # async def setup_hook(self):
    #     # Sync slash commands globally (can take a few minutes to appear)
    #     await self.tree.sync()
    #     print("Command tree synced")

    async def setup_hook(self):
        
        self.tree.add_command(groups_command_group)
        self.tree.add_command(settings_group)
        
        guild_id = int(config.DEV_GUILD_ID)
        if guild_id:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {guild_id}.")
        else:
            await self.tree.sync()
            print("Slash command tree synced globally.")

bot = HabitBot()

@bot.event
async def on_ready():
    database.init()
    print(f"Logged in as {bot.user} (id={bot.user.id})")
    

@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=True)

# TODO Create a help command with usage info

bot.run(config.DISCORD_TOKEN)