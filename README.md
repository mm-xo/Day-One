# Day One

Day One is a Discord habit accountability bot. It helps users create habit groups, check in daily, track streaks, and stay accountable with friends.

## Features

- Create and join habit accountability groups
- Daily group check-ins
- Streak tracking
- Group leaderboards
- Personal and member stats
- User timezone support
- Allowed skip days for habit groups
- Developer testing commands
- SQLite database storage
- Docker deployment support
- Automated backups
- GitHub Actions CI

## Commands

### General Commands

| Command | Description |
|---|---|
| `/help` | Show the main help menu and command overview |

### User Commands

| Command | Description |
|---|---|
| `/user set_timezone` | Set your timezone so daily check-ins reset correctly for your local day |

### Group Commands

| Command | Description |
|---|---|
| `/group create` | Create a new habit group |
| `/group join` | Join an existing habit group |
| `/group leave` | Leave a group you are currently in |
| `/group list` | View available habit groups |
| `/group checkin` | Complete your daily check-in for a group |
| `/group leaderboard` | View the group leaderboard |
| `/group stats` | View your group stats, or optionally view another member’s stats |

### Developer Commands

Developer commands are intended for testing and maintenance. They should only be available in the configured development server.

| Command | Description |
|---|---|
| `/dev help` | Show developer command help |
| `/dev reset` | Reset development/test data |
| `/dev seed_group` | Create a test habit group |
| `/dev set_today` | Manually set the bot’s current test date |
| `/dev advance_days` | Move the test date forward by a number of days |
| `/dev show_states` | Show internal streak/check-in state for debugging |
| `/dev checkin_as` | Perform a test check-in as another user |

## Tech Stack

- Python 3.12
- discord.py
- SQLite
- aiosqlite
- pytest
- Docker
- GitHub Actions

## Local Setup

Use this section if you want to run the bot locally for development.

### Requirements

Make sure you have the following installed:

* Python 3.12
* uv
* Git

### Clone the Repository

```bash
git clone https://github.com/mm-xo/Day-One.git
cd Day-One
```

### Create a `.env` File

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
DEV_GUILD_ID=your_dev_server_id
DEV_USER_IDS=123456789012345678,987654321098765432
ADMIN_ROLES=Admin,Mod
DISCORD_LOG_CHANNEL_ID=your_log_channel_id
LOG_LEVEL=INFO
SYNC_GLOBAL_COMMANDS=true
```

`DISCORD_TOKEN` is required. This is the token for your Discord bot.

`DEV_GUILD_ID` is the Discord server ID used for development/testing.

`DEV_USER_IDS` is a comma-separated list of Discord user IDs that are allowed to use developer commands.

`ADMIN_ROLES` is a comma-separated list of role names that are allowed to use admin-level commands.

`DISCORD_LOG_CHANNEL_ID` is the Discord channel ID where bot logs should be sent.

`LOG_LEVEL` controls the logging level. For normal use, keep it as `INFO`.

`SYNC_GLOBAL_COMMANDS` controls whether normal slash commands are synced globally. Use `true` for production/global command sync, and `false` if you only want to sync commands to the development server.


### Install Dependencies

```bash
uv sync
```

### Run the Bot Locally

```bash
uv run python src/bot.py
```

## Testing

Run all tests with:

```bash
uv run pytest
```

## Production Deployment

This project is deployed on an Oracle Cloud Ubuntu server using Docker Compose.

Docker can run on any machine with Docker installed, but these commands are mainly intended for the production server.

Start or rebuild the bot:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

Stop the bot:

```bash
docker compose down
```

Restart the bot:

```bash
docker compose restart
```

## Backups

The bot stores its SQLite database in the `data/` folder.

Automatic backups are stored in the `backups/` folder. These backups help protect habit group, check-in, and streak data if the production database ever needs to be restored.

## CI/CD

This project uses GitHub Actions for continuous integration.

Whenever code is pushed to GitHub, the test suite runs automatically to make sure the bot still works correctly before changes are deployed.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for more details.
