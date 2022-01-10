from datetime import datetime, timezone
from difflib import SequenceMatcher

import discord  # type: ignore
from discord import slash  # type: ignore
from discord import ui # type: ignore

class Confirm(ui.View):
    def __init__(self, *args, **kwargs):
        self.value = False
        super().__init__(*args, **kwargs)

    @ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, _, interaction):
        await interaction.response.defer()
        self.value = True
        self.stop()
    
    @ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, _, interaction):
        await interaction.response.defer()
        self.stop()


class Banking(slash.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash.slash_command(
        name="balance",
        description="View how much money you and organisations that you own have",
        guild_id=907657508292792342,
    )
    async def balance(self, interaction):
        if not str(interaction.user.id) in self.bot.data["banking"]["users"]:
            balance = 0
            self.bot.data["banking"]["users"][str(interaction.user.id)] = 0
        else:
            balance = self.bot.data["banking"]["users"][str(interaction.user.id)]

        orgs = []
        for name, org in self.bot.data["banking"]["organisations"].items():
            if org["owner"] == str(interaction.user.id):
                orgs.append(
                    dict(balance=org["balance"], name=name)
                )

        content = f"You have {balance} 🪙\n"
        for n, org in enumerate(orgs, start=1):
            content += f"\n{n}. {org['name']} - {org['balance']} 🪙"

        await interaction.response.send_message(content=content, ephemeral=True)

    async def org_autocomplete(self, _, value):
        orgs = [o for o in self.bot.data["banking"]["organisations"]]
        return sorted(orgs, key=lambda o: SequenceMatcher(None, value, o).ratio())

    async def my_orgs(self, interaction, value):
        orgs = [
            n
            for n, o in self.bot.data["banking"]["organisations"].items()
            if str(interaction.user.id) == o["owner"]
        ]
        return sorted(orgs, key=lambda o: SequenceMatcher(None, value, o).ratio())

    @slash.slash_command(
        name="pay",
        description="Pay someone cheesecoins",
        guild_id=907657508292792342,
    )
    async def pay(self):
        ...

    @pay.command(name="user", description="Pay a user some cheesecoin")
    @slash.option(
        "anonymous",
        description="Should transaction be anonymous?",
        required=False,
    )
    @slash.option(
        "organisation",
        description="An organisation you own who it is coming from",
        required=False,
        autocomplete=my_orgs
    )
    @slash.option("amount", description="The amount of cheesecoin you wish to pay them")
    @slash.option("payee", description="The user you want to pay your cheesecoin to")
    async def pay_user(
        self,
        interaction,
        payee: discord.User,
        amount: float,
        organisation: str = None,
        anonymous: bool = False,
    ):
        if not str(interaction.user.id) in self.bot.data["banking"]["users"]:
            await interaction.response.send_message(
                "You currently are not registered in my database, run `/balance` to give yourself 0 🪙",
                ephemeral=True,
            )
            return
        if organisation is not None and (
            not organisation in self.bot.data["banking"]["organisations"]
            or self.bot.data["banking"]["organisations"][organisation]["owner"]
            != str(interaction.user.id)
        ):
            await interaction.response.send_message(
                "That organisation doesn't exist or you don't own it",
                ephemeral=True,
            )
            return

        if (
            organisation is None
            and self.bot.data["banking"]["users"][str(interaction.user.id)] < amount
        ):
            await interaction.response.send_message(
                "You don't have enough 🪙 to pay for that", ephemeral=True
            )
            return
        elif (
            organisation is not None
            and self.bot.data["banking"]["organisations"][organisation]["balance"]
            < amount
        ):
            await interaction.response.send_message(
                "{organisation} doesn't have enough 🪙 to pay for that", ephemeral=True
            )
            return

        if str(payee.id) in self.bot.data["banking"]["users"]:
            self.bot.data["banking"]["users"][str(payee.id)] += amount
        else:
            self.bot.data["banking"]["users"][str(payee.id)] = amount

        if organisation is None:
            self.bot.data["banking"]["users"][str(interaction.user.id)] -= amount
        else:
            self.bot.data["banking"]["organisations"][organisation]["balance"] -= amount

        receiver = (
            (str(interaction.user) if organisation is None else organisation)
            if not anonymous
            else "Anon."
        )

        await payee.send(content=f"You have received {amount} from {receiver}")
        await interaction.response.send_message(
            content=f"You have paid {payee!s} {amount} 🪙",
            ephemeral=True,
        )

    @pay.command(name="organisation", description="Pay an organisation some cheesecoin")
    @slash.option(
        "anonymous",
        description="Should transaction be anonymous?",
        required=False,
    )
    @slash.option(
        "organisation",
        description="An organisation you own who it is coming from",
        required=False,
        autocomplete=my_orgs
    )
    @slash.option("amount", description="The amount of cheesecoint you want to pay")
    @slash.option(
        "payee",
        description="The organisation you wish to pay cheesecoin to",
        autocomplete=org_autocomplete,
    )
    async def pay_org(
        self,
        interaction,
        payee: str,
        amount: float,
        organisation: str = None,
        anonymous: bool = False,
    ):
        if not str(interaction.user.id) in self.bot.data["banking"]["users"]:
            await interaction.response.send_message(
                "You currently are not registered in my database, run `/balance` to give yourself 0 🪙",
                ephemeral=True,
            )
            return
        if organisation is not None and (
            not organisation in self.bot.data["banking"]["organisations"]
            or self.bot.data["banking"]["organisations"][organisation]["owner"]
            != str(interaction.user.id)
        ):
            await interaction.response.send_message(
                "That organisation doesn't exist or you don't own it",
                ephemeral=True,
            )
            return

        if (
            organisation is None
            and self.bot.data["banking"]["users"][str(interaction.user.id)] < amount
        ):
            await interaction.response.send_message(
                "You don't have enough 🪙 to pay for that", ephemeral=True
            )
            return
        elif (
            organisation is not None
            and self.bot.data["banking"]["organisations"][organisation]["balance"]
            < amount
        ):
            await interaction.response.send_message(
                "{organisation} doesn't have enough 🪙 to pay for that", ephemeral=True
            )
            return

        self.bot.data["banking"]["organisations"][payee]["balance"] += amount

        if organisation is None:
            self.bot.data["banking"]["users"][str(interaction.user.id)] -= amount
        else:
            self.bot.data["banking"]["organisations"][organisation]["balance"] -= amount

        owner = await self.bot.fetch_user(
            self.bot.data["banking"]["organisations"][payee]["owner"]
        )

        receiver = (
            (str(interaction.user) if organisation is None else organisation)
            if not anonymous
            else "Anon."
        )

        await owner.send(content=f"You have received {amount} from {receiver}")
        await interaction.response.send_message(
            content=f"You have paid {payee} {amount} 🪙",
            ephemeral=True,
        )

    @slash.slash_command(
        name="claimrollcall",
        description="Claims your MP rollcall for the day",
        guild_id=907657508292792342,
        default_permission=False
    )
    @slash.permission(
        912022899806855178, type=discord.Role, allow=True
    )
    async def claimrollcall(self, interaction):
        now = int(datetime.now(timezone.utc).timestamp())
        if (not str(interaction.user.id) in self.bot.data["banking"]["rollcall"]) or (
            now - self.bot.data["banking"]["rollcall"][str(interaction.user.id)]
        ) >= 86400:
            self.bot.data["banking"]["rollcall"][str(interaction.user.id)] = now

            if str(interaction.user.id) in self.bot.data["banking"]["users"]:
                self.bot.data["banking"]["users"][str(interaction.user.id)] += 2
            else:
                self.bot.data["banking"]["users"][str(interaction.user.id)] = 2

            await interaction.response.send_message(
                content="Successfully claimed rollcall!",
                ephemeral=True,
            )

        else:
            ago = self.bot.data["banking"]["rollcall"][str(interaction.user.id)]
            await interaction.response.send_message(
                content=f"Sorry, you last claimed your rollcall <t:{ago}:R>, please wait a little longer",
                ephemeral=True,
            )
    
    @slash.slash_command(
        name="org",
        description="Organisation-related commands",
        guild_id=907657508292792342
    )
    async def org(self):
        ...
    
    @org.command(name="create", description="Create an organisation")
    @slash.option("name", description="The name of your new organisation")
    async def org_create(self, interaction, name: str):
        if name in self.bot.data["banking"]["organisations"]:
            await interaction.response.send_message(
                content=f"An organisation with the name {name} already exists",
                ephemeral=True,
            )
            return
        
        self.bot.data["banking"]["organisations"][name] = {
            "balance": 0,
            "owner": str(interaction.user.id)
        }
        await interaction.response.send_message(
            content=f"Successfully created {name}!",
            ephemeral=True,
        )
    
    @org.command(name="edit", description="Edit an organisation")
    @slash.option("name", description="Change the name", required=False)
    @slash.option("owner", description="Change who owns the organisation", required=False)
    @slash.option("org", description="The name of the organisation that you want to edit", autocomplete=my_orgs)
    async def org_edit(self, interaction, org: str, owner: discord.User = None, name: str = None):
        if not org in self.bot.data["banking"]["organisations"] or self.bot.data["banking"]["organisations"][org]["owner"] != str(interaction.user.id):
            await interaction.response.send_message(
                content=f"An organisation with the name {org} does not exist, or you do not own it",
                ephemeral=True,
            )
            return
        
        if owner is not None:
            self.bot.data["banking"]["organisations"][org]["owner"] = str(owner.id)
        if name is not None:
            self.bot.data["banking"]["organisations"][name] = self.bot.data["banking"]["organisations"][org]
            del self.bot.data["banking"]["organisations"][org]
        
        await interaction.response.send_message(
            content=f"Successfully applied changes to {org}",
            ephemeral=True,
        )
    
    @org.command(name="delete", description="Delete an organisation that you own")
    @slash.option("org", description="The name of the organisation that you want to edit", autocomplete=my_orgs)
    async def org_delete(self, interaction, org: str):
        if not org in self.bot.data["banking"]["organisations"] or self.bot.data["banking"]["organisations"][org]["owner"] != str(interaction.user.id):
            await interaction.response.send_message(
                content=f"An organisation with the name {org} does not exist, or you do not own it",
                ephemeral=True,
            )
            return
        
        view = Confirm(timeout=60)
        await interaction.response.send_message(content=f"Are you sure you want to delete {org}", view=view, ephemeral=True)

        await view.wait()
        await interaction.edit_original_message(view=None)

        if view.value:
            del self.bot.data["banking"]["organisations"][org]

            await interaction.followup.send(
                content=f"Successfully deleted {org}",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                content="Aborted.",
                ephemeral=True
            )

    @slash.slash_command(
        name="sudo",
        description="Super-user commands, do not touch!",
        guild_id=907657508292792342,
        default_permission=False
    )
    @slash.permission(737928480389333004, type=discord.User, allow=True)
    @slash.permission(907660552938061834, type=discord.Role, allow=True)
    @slash.permission(922878833080799242, type=discord.Role, allow=True)
    @slash.permission(922883235648774165, type=discord.Role, allow=True)
    async def sudo(self):
        ...


def setup(bot):
    bot.add_cog(Banking(bot))
