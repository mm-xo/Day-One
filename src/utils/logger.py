from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import discord

import config


LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "day_one.log"

_discord_handler: DiscordLogHandler | None = None


class DiscordLogHandler(logging.Handler):
    """
    Logging handler that sends WARNING/ERROR/CRITICAL logs
    to a Discord channel.

    Keep this handler for important logs only.
    Do not spam info/debug logs into Discord.
    """

    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id
        self.bot: discord.Client | None = None

    def set_bot(self, bot: discord.Client):
        self.bot = bot

    def emit(self, record: logging.LogRecord):
        if self.bot is None:
            return

        if self.channel_id == 0:
            return

        if self.bot.loop.is_closed():
            return

        try:
            message = self.format(record)

            # Discord message limit is 2000 chars.
            # Keep some room for code block formatting.
            if len(message) > 1800:
                message = message[:1800] + "\n...truncated"

            self.bot.loop.create_task(self._send_log(message))

        except Exception:
            self.handleError(record)

    async def _send_log(self, message: str):
        if self.bot is None:
            return

        try:
            await self.bot.wait_until_ready()

            channel = self.bot.get_channel(self.channel_id)

            if channel is None:
                channel = await self.bot.fetch_channel(self.channel_id)

            if not isinstance(
                channel,
                discord.TextChannel | discord.Thread | discord.DMChannel,
            ):
                return

            await channel.send(f"```log\n{message}\n```")

        except Exception:
            # Do not log from here.
            # Otherwise, failed log sending can cause recursive logging.
            pass


def setup_logging() -> logging.Logger:
    """
    Sets up app-wide logging.

    Logs go to:
    - console
    - logs/day_one.log
    - Discord channel for WARNING and above
    """

    global _discord_handler

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("day_one")
    logger.setLevel(config.LOG_LEVEL)

    # Avoid duplicate handlers when tests/imports reload modules.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.LOG_LEVEL)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(config.LOG_LEVEL)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    if config.DISCORD_LOG_CHANNEL_ID:
        discord_handler = DiscordLogHandler(config.DISCORD_LOG_CHANNEL_ID)
        discord_handler.setLevel(logging.WARNING)
        discord_handler.setFormatter(formatter)

        logger.addHandler(discord_handler)
        _discord_handler = discord_handler

    return logger


def set_discord_bot(bot: discord.Client):
    """
    Gives the Discord log handler access to the running bot.
    Call this in bot.py after bot is created.
    """

    if _discord_handler is not None:
        _discord_handler.set_bot(bot)


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None:
        return logging.getLogger("day_one")

    return logging.getLogger(f"day_one.{name}")