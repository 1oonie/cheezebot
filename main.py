import sys

sys.path.append("./discord.py")

import discord  # type: ignore

from pipe import where, map
import matplotlib.pyplot as plt

import slash_util

from io import BytesIO
from collections import defaultdict
from functools import partial
from textwrap import indent
import traceback

from config import *


def pie_chart(*args, **kwargs):
    buffer = BytesIO()
    fig, ax = plt.subplots()
    ax.pie(*args, **kwargs)
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return discord.File(buffer, filename="pie.png")


class TockTick(slash_util.ApplicationCog):
    @slash_util.slash_command(
        name="stats",
        description="Stats about tock tick posters",
        guild_id=907657508292792342,
    )
    async def _stats(self, ctx):
        interaction = ctx.interaction
        await interaction.response.defer(ephemeral=True)

        messages = (
            await interaction.guild.get_channel(916431428693135360)
            .history(limit=100)
            .flatten()
        ) | where(lambda m: len(m.attachments) != 0 and not (m.attachments[0].height is None or m.attachments[0].height < 100))

        async def count_emoji(emoji, reactions):
            count = 0
            for r in reactions:
                users = await r.users().flatten()
                if not r.emoji == emoji:
                    continue

                if r.message.author in users:
                    count -= 1
                count += r.count
            return count

        reaction_count = defaultdict(int)
        for message in messages:
            reaction_count[message.author.name] += await count_emoji(
                "👍", message.reactions
            )

        s = sum(v for v in reaction_count.values() if v >= 0)

        data = defaultdict(int)
        for r in reaction_count:
            if reaction_count[r] <= 0:
                continue

            data[r] = reaction_count[r] * (360 / s)  # type: ignore

        fn = partial(
            pie_chart,
            list(data.values()),
            labels=list(data.keys()),
            startangle=90,
            shadow=True,
        )
        file = await ctx.bot.loop.run_in_executor(None, fn)

        await interaction.edit_original_message(
            content="```"
            + "\n".join(f"{r}: {reaction_count[r]}" for r in reaction_count)
            + "```",
            file=file,
        )


class Bot(slash_util.Bot):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.add_cog(TockTick(self))

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.login(token)

        app_info = await self.application_info()
        self._connection.application_id = app_info.id

        await self.delete_all_commands(guild_id=GUILD_ID)

        await self.sync_commands()
        await self.connect(reconnect=reconnect)

    async def on_ready(self):
        print(f"logged in as {self.user!s}")

    async def close(self):
        return await super().close()

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id == 916431428693135360:
            if not len(message.attachments) == 0:
                if not (message.attachments[0].height is None or message.attachments[0].height < 100):

                    await message.add_reaction("👍")
                    await message.add_reaction("👎")

        if message.author.id == 737928480389333004:
            if message.content.startswith("```py"):
                env = {}
                env.update(globals())
                env.update(locals())

                clean_content = "async def func():\n" + indent(
                    message.content.strip("```py"), "    "
                )
                try:
                    exec(clean_content, env)
                    await env["func"]()
                except:
                    await message.channel.send(
                        "```py\n" + traceback.format_exc() + "```"
                    )


bot = Bot(command_prefix="!")

bot.run(TOKEN)
