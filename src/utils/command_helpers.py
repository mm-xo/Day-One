import discord
import math

# ============================================================================================
def validate_role(interaction, accepted_roles):
    roles = interaction.user.roles # list of roles
    for role in roles:
        if role.name in accepted_roles:
            return True
    return False
# ============================================================================================


# ============================================================================================
async def is_command_in_server(interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in a server.", ephemeral=True)
        return False
    return True
# ============================================================================================


# ============================================================================================
async def get_leaderboard_display_names(
    guild: discord.Guild,
    rows,
) -> dict[int, str]:
    display_names = {}

    for row in rows:
        user_id = int(row["user_id"])

        member = guild.get_member(user_id)

        if member is None:
            try:
                member = await guild.fetch_member(user_id)
            except discord.HTTPException:
                member = None

        display_names[user_id] = member.display_name if member else f"User {user_id}"

    return display_names
# ============================================================================================


# ============================================================================================
LEADERBOARD_PAGE_SIZE = 5


def _days_text(days: int) -> str:
    if days <= 0:
        return "No streak"
    if days == 1:
        return "1 day"
    return f"{days} days"


def build_leaderboard_embed(
    group_name: str,
    rows,
    display_names: dict[int, str],
    page: int = 0,
    page_size: int = LEADERBOARD_PAGE_SIZE,
) -> discord.Embed:
    rows = list(rows)

    total_members = len(rows)
    total_pages = max(1, math.ceil(total_members / page_size))

    start = page * page_size
    end = start + page_size
    page_rows = rows[start:end]

    embed = discord.Embed(
        title=f"{group_name} Leaderboard",
        description="Ranked by current streak, weekly check-ins, and best streak.",
        color=discord.Color.green(),
    )

    if not page_rows:
        embed.add_field(
            name="No members yet",
            value="Nobody has joined this group yet.",
            inline=False,
        )
        return embed

    for index, row in enumerate(page_rows, start=start + 1):
        user_id = int(row["user_id"])
        name = display_names.get(user_id, f"User {user_id}")

        current_streak = row["current_streak"]
        best_streak = row["best_streak"]
        weekly_checkins = row["weekly_checkins"]
        last_checkin = row["last_checkin"] or "Never"

        embed.add_field(
            name=f"#{index} — {name}",
            value=(
                f"Current streak: **{_days_text(current_streak)}**\n"
                f"This week: **{weekly_checkins}/7**\n"
                f"Best streak: **{_days_text(best_streak)}**\n"
                f"Last check-in: `{last_checkin}`\n"
                f"\u200b"
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"Page {page + 1}/{total_pages} • "
            f"Showing {start + 1}-{min(end, total_members)} of {total_members}"
        )
    )

    return embed


class LeaderboardPaginationView(discord.ui.View):
    def __init__(
        self,
        group_name: str,
        rows,
        display_names: dict[int, str],
        page_size: int = LEADERBOARD_PAGE_SIZE,
    ):
        super().__init__(timeout=120)

        self.group_name = group_name
        self.rows = list(rows)
        self.display_names = display_names
        self.page_size = page_size
        self.page = 0
        self.total_pages = max(1, math.ceil(len(self.rows) / self.page_size))

        self._sync_buttons()

    def make_embed(self) -> discord.Embed:
        return build_leaderboard_embed(
            group_name=self.group_name,
            rows=self.rows,
            display_names=self.display_names,
            page=self.page,
            page_size=self.page_size,
        )

    def _sync_buttons(self):
        for item in self.children:
            if not isinstance(item, discord.ui.Button):
                continue

            if item.custom_id == "leaderboard_previous":
                item.disabled = self.page <= 0

            elif item.custom_id == "leaderboard_next":
                item.disabled = self.page >= self.total_pages - 1

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        custom_id="leaderboard_previous",
    )
    async def previous_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.page -= 1
        self._sync_buttons()

        await interaction.response.edit_message(
            embed=self.make_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.secondary,
        custom_id="leaderboard_next",
    )
    async def next_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.page += 1
        self._sync_buttons()

        await interaction.response.edit_message(
            embed=self.make_embed(),
            view=self,
        )
# ============================================================================================


# ============================================================================================
def _yes_no(value) -> str:
    return "Yes" if value else "No"


def build_group_stats_embed(
    group_name: str,
    display_name: str,
    stats_row,
) -> discord.Embed:
    current_streak = stats_row["current_streak"]
    best_streak = stats_row["best_streak"]
    weekly_checkins = stats_row["weekly_checkins"]
    total_checkins = stats_row["total_checkins"]
    last_checkin = stats_row["last_checkin"] or "Never"
    joined_at = stats_row["joined_at"] or "Unknown"
    checked_in_today = stats_row["checked_in_today"]

    embed = discord.Embed(
        title=f"{display_name}'s Stats",
        description=f"Progress in **{group_name}**",
        color=discord.Color.green(),
    )

    embed.add_field(
        name="Streaks",
        value=(
            f"Current streak: **{_days_text(current_streak)}**\n"
            f"Best streak: **{_days_text(best_streak)}**\n"
            f"Last check-in: `{last_checkin}`"
        ),
        inline=False,
    )

    embed.add_field(
        name="Activity",
        value=(
            f"This week: **{weekly_checkins}/7**\n"
            f"Total check-ins: **{total_checkins}**\n"
            f"Checked in today: **{_yes_no(checked_in_today)}**"
        ),
        inline=False,
    )

    embed.set_footer(text=f"Joined group: {joined_at}")

    return embed
# ============================================================================================