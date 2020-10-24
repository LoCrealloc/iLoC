from discord.ext.commands import Cog, command, Bot, Context
from embedcreator import infoembed


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

    @command(name="info", aliases=["infos", "information"])
    async def info(self, ctx: Context):
        """
        Gives you some information about the iLoC
        """
        embed = await infoembed(self.bot, ctx.message)
        await ctx.channel.send(embed=embed)
