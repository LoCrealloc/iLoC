from discord.ext.commands import Cog, command, Bot, has_permissions, Context
from embedcreator import infoembed
from discord import Guild


class Information(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name="ping")
    async def ping(self, ctx: Context):
        """
        Displays the bot latency
        """
        latency = str(self.bot.latency * 100).split(".")[0]
        await ctx.channel.send(f"Pong! {latency} ms")

    @command(name="info", aliases=["infos", "about"])
    async def info(self, ctx: Context):
        """
        Gives you some information about the iLoC
        """
        embed = await infoembed(self.bot, ctx.message)
        await ctx.channel.send(embed=embed)
