import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

intents = discord.Intents.default()

class HabitBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)

    # async def setup_hook(self):
    #     # Sync slash commands globally (can take a few minutes to appear)
    #     await self.tree.sync()
    #     print("Command tree synced")

    async def setup_hook(self):
        guild_id = int(os.getenv("DEV_GUILD_ID", "0"))
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
    print(f"Logged in as {bot.user} (id={bot.user.id})")

@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=True)

bot.run(TOKEN)