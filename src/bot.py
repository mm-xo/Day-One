import discord
from discord.ext import commands
import config
import database
from commands.groups import group as groups_command_group
from commands.user import user_group
from commands.dev import dev_group

intents = discord.Intents.default()

class HabitBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await database.init(bot)
        
        self.tree.add_command(groups_command_group)
        self.tree.add_command(user_group)
        
        guild_id = int(config.DEV_GUILD_ID)
        
        if guild_id:
            guild = discord.Object(id=guild_id)
            # Copy normal global commands to dev guild
            self.tree.copy_global_to(guild=guild)
            
            # add dev commands ONLY to dev guild
            self.tree.add_command(dev_group, guild=guild)
            
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {guild_id}.")
        else:
            # No dev guild means do NOT register dev commands
            await self.tree.sync()
            print("Slash command tree synced globally.")

    async def close(self):
        print("Closing bot...")
        await database.close()
        await super().close()

bot = HabitBot()

@bot.event
async def on_ready():
    user = bot.user
    if user is None:
        raise RuntimeError("Bot is not initialized")
    print(f"Logged in as {user} (id={user.id})")
    

@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong", ephemeral=True)

# TODO Create a help command with usage info

async def main():
    token = config.DISCORD_TOKEN
    if token is None:
        raise ValueError("DISCORD_TOKEN must be set")
    # bot.run(token)
    async with bot:
        await bot.start(token)

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by Ctrl+C.")
    # main()