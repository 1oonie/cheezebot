from datetime import datetime, timedelta, timezone

import discord  # type: ignore
from discord import slash  # type: ignore
from discord.http import Route  # type: ignore


class Police(slash.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash.slash_command(
        name="imprison",
        description="Imprison (time out) someone for x number of days",
        guild_id=907657508292792342,
        default_permission=False,
    )
    @slash.option(
        "reason",
        description="Why this user is being imprisoned (shows up on the audit log)",
    )
    @slash.option("days", description="How many days you want to imprison them for")
    @slash.option("user", description="The user you want to imprison")
    @slash.permission(737928480389333004, type=discord.User, allow=True)
    @slash.permission(922883079738126356, type=discord.Role, allow=True)
    async def imprison(
        self, interaction, user: discord.User, days: slash.Range[1, 28], reason: str
    ):
        expires = datetime.now(timezone.utc) + timedelta(days=days)
        data = {"communication_disabled_until": expires.isoformat()}

        r = Route(
            "PATCH",
            "/guilds/{guild_id}/members/{user_id}",
            guild_id=interaction.guild.id,
            user_id=user.id,
        )
        await self.bot.http.request(r, json=data, reason=reason)

        await interaction.response.send_message(
            f"{user!s} has been imprisoned by {interaction.user!s}! They will be released in <t:{round(expires.timestamp())}:R>"
        )

    @slash.slash_command(
        name="release",
        description="Release someone from prison (remove their timeout)",
        guild_id=907657508292792342,
        default_permission=False,
    )
    @slash.option(
        "reason",
        description="Why this user is being released (shows up on the audit log)",
    )
    @slash.option("user", description="The user you want to release")
    @slash.permission(737928480389333004, type=discord.User, allow=True)
    @slash.permission(922883079738126356, type=discord.Role, allow=True)
    async def release(self, interaction, user: discord.User, reason: str):
        r = Route(
            "PATCH",
            "/guilds/{guild_id}/members/{user_id}",
            guild_id=interaction.guild.id,
            user_id=user.id,
        )
        await self.bot.http.request(
            r, json={"communication_disabled_until": None}, reason=reason
        )

        await interaction.response.send_message(
            f"{user!s} has been released from prison by {interaction.user!s}."
        )


def setup(bot):
    bot.add_cog(Police(bot))
