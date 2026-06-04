import discord
from discord.ext import commands
import config
import database
from commands.groups import group as groups_command_group
from commands.user import user_group

intents = discord.Intents.default()

class HabitBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        
        self.tree.add_command(groups_command_group)
        self.tree.add_command(user_group)
        
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
    await database.init(bot)
    user = bot.user
    if user is None:
        raise RuntimeError("Bot user is not initialized")
    print(f"Logged in as {user} (id={user.id})")
    

@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=True)

# TODO Create a help command with usage info

def main():
    token = config.DISCORD_TOKEN
    if token is None:
        raise ValueError("DISCORD_TOKEN must be set")
    bot.run(token)

if __name__ == "__main__":
    main()