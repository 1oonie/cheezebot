import random

import discord  # type: ignore
from discord import slash  # type: ignore
from discord import ui  # type: ignore

FLOWERS = ["🌺", "🌷", "🌼"]
FISH = {"🐟": 1, "🐠": 5, "🐡": 3, "🦞": 3, "🦀": 4, "🐳": 10}
SHARK = "🦈"
OBJECTS = ["👢", "⚓"]


class StaticButton(ui.Button):
    def __init__(self, emoji=None):
        super().__init__(label="\u200b", emoji=emoji, style=discord.ButtonStyle.green)

    async def callback(self, interaction):
        self.disabled = True
        await interaction.response.edit_message(
            view=self.view,
        )


class WaterButton(ui.Button):
    def __init__(self, count, emoji):
        self.value = emoji
        self.count = count
        super().__init__(label="/" * count, style=discord.ButtonStyle.primary)

    async def callback(self, interaction):
        self.view.picked_up.append(self.value)
        picked_up = ", ".join(self.view.picked_up)

        self.count -= 1
        self.label = "/" * self.count

        if self.count == 0:
            self.disabled = True
            self.label = self.value

        self.view.tries_remaining -= 1

        if self.value == SHARK:
            self.view.disable_all()
            self.view.stop()
            await interaction.response.edit_message(
                view=self.view,
            )
            await interaction.followup.send(
                content=f"Oh no! You hit a {SHARK} :( Your score was {self.view.score}"
            )
            return

        elif self.value in OBJECTS:
            await interaction.response.edit_message(
                content=f"You fished up a {self.value}, it is pretty worthless so you won't get anything from it.\n\nItems fished up so far: {picked_up}\nGoes remaining: {self.view.tries_remaining}\nScore: {self.view.score}",
                view=self.view,
            )

        else:
            self.view.score += FISH[self.value]
            await interaction.response.edit_message(
                content=f"You fished up a {self.value}, you get {FISH[self.value]} points for that!\n\nItems fished up so far: {picked_up}\nGoes remaining: {self.view.tries_remaining}\nScore: {self.view.score}",
                view=self.view,
            )

        self.value = WaterButton.get_emoji()

        if self.view.tries_remaining == 0:
            self.view.stop()
            self.view.disable_all()

            await self.view.message.edit(view=self.view)
            await interaction.followup.send(
                f"Your game is over! You scored a total of {self.view.score} points without hitting a shark!"
            )

    @staticmethod
    def get_emoji():
        return random.choice(
            random.choices([list(FISH.keys()), SHARK, OBJECTS], weights=[2, 0.1, 0.75])[
                0
            ]
        )


class FishingView(ui.View):
    def __init__(self, author, *args, **kwargs):
        self.author = author

        super().__init__(*args, **kwargs)

        for _ in range(25):
            type_ = random.choices([WaterButton, StaticButton], weights=[1, 0.6])[0]
            if type_ is StaticButton:
                instance = StaticButton(
                    emoji=random.choices(
                        [None, random.choice(FLOWERS)], weights=[1, 2]
                    )[0]
                )
            else:
                instance = WaterButton(
                    emoji=WaterButton.get_emoji(), count=random.randint(1, 3)
                )

            self.add_item(instance)

        self.tries_remaining = 10
        self.score = 0
        self.picked_up = []

    def disable_all(self):
        for child in self.children:
            child.disabled = True

    async def interaction_check(self, interaction):
        if interaction.user.id == self.author.id:
            return True
        else:
            await interaction.response.send_message(
                content="This is not your game of fishing!", ephemeral=True
            )
            return False

    async def on_timeout(self):
        await self.message.edit(
            content=f"Timed out due to lack of interaction, score was {self.score}",
            view=None,
        )


class Fishing(slash.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash.slash_command(
        name="fish",
        description="Basically made to annoy Yo! Bot, please enjoy",
        guild_id=907657508292792342,
    )
    async def fish(self, interaction):
        view = FishingView(interaction.user, timeout=60)
        await interaction.response.send_message(content="Play fishing!", view=view)
        view.message = await interaction.original_message()


def setup(bot):
    bot.add_cog(Fishing(bot))
