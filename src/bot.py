import discord
from discord.ext import commands
import config
import database
from commands.groups import group as groups_command_group
from commands.user import user_group
from commands.dev import dev_group
from commands.help import help_command
from utils.logger import setup_logging, set_discord_bot, get_logger

logger = setup_logging()

intents = discord.Intents.default()

class HabitBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await database.init(bot)
        
        self.tree.add_command(groups_command_group)
        self.tree.add_command(user_group)
        self.tree.add_command(help_command)
        
        dev_guild_id = int(config.DEV_GUILD_ID or 0)
        sync_global = config.SYNC_GLOBAL_COMMANDS
        
        if sync_global:
            await self.tree.sync()
            logger.info("Global slash commands synced.")
        
        if dev_guild_id:
            guild = discord.Object(id=dev_guild_id)
            
            # copy public commands to dev guild
            self.tree.copy_global_to(guild=guild)
            
            # add dev commands only to dev guild
            self.tree.add_command(dev_group, guild=guild)
            
            await self.tree.sync(guild=guild)
            logger.info(f"Dev slash commands synced to guild {dev_guild_id}.")

    async def close(self):
        logger.info("Closing bot...")
        await database.close()
        await super().close()

bot = HabitBot()
set_discord_bot(bot)

@bot.event
async def on_ready():
    user = bot.user
    if user is None:
        raise RuntimeError("Bot is not initialized")
    
    logger.info(f"Logged in as {user} (id={user.id})")


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError,
):
    command_name = interaction.command.name if interaction.command else "unknown"

    logger.error(
        "Slash command failed: command=%s user_id=%s guild_id=%s error_type=%s error=%s",
        command_name,
        interaction.user.id if interaction.user else "unknown",
        interaction.guild_id,
        type(error).__name__,
        error,
        exc_info=error,
    )

    message = (
        "Something went wrong while running this command. "
        "The error has been logged."
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception as send_error:
        logger.error(
            "Failed to send command error response: command=%s error=%s",
            command_name,
            send_error,
            exc_info=send_error,
        )
        

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