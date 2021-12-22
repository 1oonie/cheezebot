import sys

sys.path.append("./discord.py")

import discord  # type: ignore
from discord import slash # type: ignore

from textwrap import indent
import traceback
import json
import asyncio

from config import *

async def save_data(bot):
    while True:
        await asyncio.sleep(60)
        with open("data.json", "w") as f:
            f.write(json.dumps(bot.data, indent=4))

class Bot(slash.Bot):
    def __init__(self, **kwargs) -> None:
        with open("data.json") as f:
            self.data = json.loads(f.read())

        super().__init__(**kwargs)

        self._save_task = self.loop.create_task(save_data(self))

    async def on_ready(self):
        print(f"logged in as {self.user!s}")
    
    async def close(self):
        self._save_task.cancel()

        with open("data.json", "w") as f:
            f.write(json.dumps(self.data, indent=4))

        await super().close()

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id == 916431428693135360:
            if not len(message.attachments) == 0:
                if not (message.attachments[0].height is None or message.attachments[0].height < 10):

                    await message.add_reaction("<:upvote:922104991869718548>")
                    await message.add_reaction("<:downvote:922104870696263680>")

                    if str(message.author.id) in self.data["followers"]:
                        for follower in self.data["followers"][str(message.author.id)]:
                            user = await self.fetch_user(follower)
                            await user.send(f"{message.author!s} has sent a new post in <#916431428693135360>! Check it out here {message.jump_url}")

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


bot = Bot()

extensions = ["tocktik", "police", "banking"]

for extension in extensions:
    bot.load_extension("cogs." + extension)

bot.run(TOKEN)
