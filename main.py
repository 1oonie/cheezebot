import sys

sys.path.append("./discord.py")

import asyncio
import json
import traceback
from textwrap import indent
from io import StringIO
from datetime import datetime, timezone

import config
import discord  # type: ignore
from discord import slash  # type: ignore
from discord.http import Route # type: ignore


async def save_data(bot):
    while True:
        await asyncio.sleep(60)
        with open("data.json", "w") as f:
            f.write(json.dumps(bot.data, indent=4))

async def apply_wealth_tax(bot):
    while True:
        now = int(datetime.now(timezone.utc).timestamp())
        if "last_wealth_tax" not in bot.data["banking"] or (bot.data["banking"]["last_wealth_tax"] - now) >= 86400:
            tax = 1 - bot.data["banking"]["wealth_tax"]

            for user in bot.data["banking"]["users"]:
                bot.data["banking"]["users"][user] *= tax
            for org in bot.data["banking"]["organisations"]:
                bot.data["banking"]["organisations"][org]["balance"] *= tax

            bot.data["banking"]["last_wealth_tax"] = now
        else:
            last = bot.data["banking"]["last_wealth_tax"]
            await asyncio.sleep((last+86400+1) - now)



class Bot(slash.Bot):
    GITHUB_TOKEN = config.GITHUB_TOKEN

    def __init__(self, **kwargs) -> None:
        with open("data.json") as f:
            self.data = json.loads(f.read())

        super().__init__(**kwargs)

        self._save_task = self.loop.create_task(save_data(self))
        self._wealth_tax = self.loop.create_task(apply_wealth_tax(self))
    

    def send_multipart_helper(
        self,
        interaction,
        *,
        files=None,
        content=None,
        tts=False,
        embed=None,
        embeds=None,
        nonce=None,
        allowed_mentions=None,
        message_reference=None,
        stickers=None,
        components=None,
        ephemeral=False,
    ):

        r = Route(
            "POST",
            "/interactions/{interaction_id}/{interaction_token}/callback",
            interaction_id=interaction.id,
            interaction_token=interaction.token,
        )
        form = []

        options = {"tts": tts}
        if content:
            options["content"] = content
        if embed:
            options["embeds"] = [embed]
        if embeds:
            options["embeds"] = embeds
        if nonce:
            options["nonce"] = nonce
        if allowed_mentions:
            options["allowed_mentions"] = allowed_mentions
        if message_reference:
            options["message_reference"] = message_reference
        if components:
            options["components"] = components
        if stickers:
            options["sticker_ids"] = stickers
        if ephemeral:
            options["flags"] = 1 << 6

        payload = {"type": 4, "data": options}

        form.append({"name": "payload_json", "value": discord.utils._to_json(payload)})
        if len(files) == 1:
            file = files[0]
            form.append(
                {
                    "name": "file",
                    "value": file.fp,
                    "filename": file.filename,
                    "content_type": "application/octet-stream",
                }
            )
        else:
            for index, file in enumerate(files):
                form.append(
                    {
                        "name": f"file{index}",
                        "value": file.fp,
                        "filename": file.filename,
                        "content_type": "application/octet-stream",
                    }
                )

        return self.http.request(r, form=form, files=files)

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
                if not (
                    message.attachments[0].height is None
                    or message.attachments[0].height < 10
                ):

                    await message.add_reaction("<:upvote:922104991869718548>")
                    await message.add_reaction("<:downvote:922104870696263680>")

                    if str(message.author.id) in self.data["followers"]:
                        for follower in self.data["followers"][str(message.author.id)]:
                            user = await self.fetch_user(follower)
                            await user.send(
                                f"{message.author!s} has sent a new post in <#916431428693135360>! Check it out here {message.jump_url}"
                            )

        if message.author.id == 737928480389333004:
            if message.content.startswith("```py"):
                env = {
                    "__builtins__": __builtins__,
                    "discord": discord,
                    "message": message,
                    "author": message.author,
                    "guild": message.guild,
                    "channel": message.channel
                }

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

extensions = ["tocktik", "police", "banking", "fishing"]

for extension in extensions:
    bot.load_extension("cogs." + extension)

@bot.slash_command(name="data", description="Sends all of the data RoboLouis has", guild_id=907657508292792342)
async def senddata(interaction):
    buffer = StringIO(json.dumps(bot.data, indent=4))
    file = discord.File(buffer, filename="data.json")
    await bot.send_multipart_helper(interaction, files=[file], ephemeral=True)

bot.run(config.TOKEN)
