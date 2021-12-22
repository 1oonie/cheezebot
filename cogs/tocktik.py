import discord  # type: ignore
from discord import slash  # type: ignore

from pipe import where, map
import matplotlib.pyplot as plt

from io import BytesIO
from collections import defaultdict
from functools import partial
from glob import glob
import random


def pie_chart(*args, **kwargs):
    buffer = BytesIO()
    _, ax = plt.subplots()
    ax.pie(*args, **kwargs)
    ax.set_title("Stats of TockTik posters")
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return discord.File(buffer, filename="pie.png")


def bar_graph(x, y):
    buffer = BytesIO()
    _, ax = plt.subplots()
    ax.bar(x, y)
    ax.set_title("Stats of TockTik posters")
    ax.set_xlabel("Names")
    ax.set_ylabel("Amount of likes")
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return discord.File(buffer, filename="bar.png")


class TockTik(slash.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash.slash_command(
        name="stats",
        description="Stats about tock tick posters",
        guild_id=907657508292792342,
    )
    @slash.option(
        "type",
        description="Which type of graph you want to use",
        choices=[
            slash.OptionChoice("Bar Graph", "bar"),
            slash.OptionChoice("Pie Chart", "pie"),
        ],
    )
    async def _stats(self, interaction, type: str):
        await interaction.response.defer(ephemeral=True)

        messages = (
            await interaction.guild.get_channel(916431428693135360)
            .history(limit=100)
            .flatten()
        ) | where(
            lambda m: len(m.attachments) != 0
            and not (m.attachments[0].height is None or m.attachments[0].height < 10)
        )

        async def count_emoji(emoji, reactions):
            count = 0
            for r in reactions:
                if isinstance(r.emoji, str):
                    if r.emoji == "👍":
                        count += r.count
                    continue

                if r.emoji.name == emoji:
                    count += r.count

            return count

        reaction_count = defaultdict(int)
        for message in messages:
            reaction_count[message.author.name] += await count_emoji(
                "upvote", message.reactions
            )

        s = sum(v for v in reaction_count.values() if v >= 0)

        pie_data = defaultdict(int)
        bar_data = [list(), list()]
        for r in reaction_count:
            if reaction_count[r] <= 0:
                continue

            bar_data[0].append(r[:7] + "..." if len(r) > 7 else r)
            bar_data[1].append(reaction_count[r])

            pie_data[r] = reaction_count[r] * (360 / s)  # type: ignore

        if type == "pie":
            fn = partial(
                pie_chart,
                list(pie_data.values()),
                labels=list(pie_data.keys()),
                startangle=90,
                shadow=True,
            )
        else:
            fn = partial(bar_graph, bar_data[0], bar_data[1])

        file = await self.bot.loop.run_in_executor(None, fn)

        adverts = glob("ads/**")
        if not adverts:
            files = [file]
        else:
            choice = random.choice(adverts)
            advert = discord.File(choice, filename="advert." + choice.split(".")[-1])
            files = [file, advert]

        await interaction.edit_original_message(
            content="```"
            + "\n".join(f"{r}: {reaction_count[r]}" for r in reaction_count)
            + "```",
            files=files,
        )

    @slash.slash_command(
        name="follow",
        description="Add, remove or list who you follow",
        guild_id=907657508292792342,
    )
    async def follow(self):
        ...

    @follow.command(name="add", description="Follow a tock tik poster")
    @slash.option("user", description="The user you want to follow")
    async def follow_add(self, interaction, user: discord.User):
        if str(user.id) not in self.bot.data["followers"]:
            self.bot.data["followers"][str(user.id)] = list()

        if str(interaction.user.id) in self.bot.data["followers"][str(user.id)]:
            content = f"You are already following {user!s}, if you want to stop following them then run `/follow remove`."
        else:
            content = f"Following {user!s}!"
            await user.send(
                f"You have a new follower, {interaction.user!s} has just started following you!"
            )

            self.bot.data["followers"][str(user.id)].append(str(interaction.user.id))

        await interaction.response.send_message(content, ephemeral=True)

    @follow.command(name="remove", description="Stop following a user")
    @slash.option("user", description="The user you want to stop following")
    async def follow_remove(self, interaction, user: discord.User):
        if (
            str(user.id) not in self.bot.data["followers"]
            or str(interaction.user.id) not in self.bot.data["followers"][str(user.id)]
        ):
            content = f"You are either not following {user!s} or they do not have any followers."
        else:
            self.bot.data["followers"][str(user.id)].remove(str(interaction.user.id))
            content = f"Sucessfully unfollowed {user!s}."
            await user.send(f"{interaction.user!s} has stopped following you :(")

        await interaction.response.send_message(content, ephemeral=True)

    @follow.command(name="list", description="Lists all the people who you follow")
    async def follow_list(self, interaction):
        users = [
            i
            for i in self.bot.data["followers"]
            if str(interaction.user.id) in self.bot.data["followers"][i]
        ]
        if users:
            content = f"You follow {len(users)} people"
            for i, u in enumerate(users, start=1):
                user = await self.bot.fetch_user(u)
                content += f"\n{i}. {user!s}"
        else:
            content = "You don't follow anyone."

        await interaction.response.send_message(content, ephemeral=True)


def setup(bot):
    bot.add_cog(TockTik(bot))
