from discord.ext.commands import Cog, command, Bot, has_permissions, Context, guild_only, group
from discord.ext import tasks
from discord import TextChannel, Message, Game, Status
import json
from embedcreator import prefixembed, channelembed, musicembed
from data import togglepausereact, stopreact, skipreact, backreact, loopreact, oneloopreact, shufflereact, ejectreact, \
                 lyricreact, redheart, blackheart


class Settings(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.presence.start()

    @group(name="settings", aliases=["preferences", "set"])
    async def settings(self, ctx: Context):
        """
        Change the bots references
        """

    @settings.command(name="prefix")
    @has_permissions(manage_channels=True)
    @guild_only()
    async def settings_prefix(self, ctx: Context, prefix: str):
        """
        Set the bots prefix
        """

        if prefix:
            with open("customs.json", "r") as customsfile:
                try:
                    customdict: dict = json.load(customsfile)
                except json.JSONDecodeError:
                    customdict = {}

            with open("customs.json", "w") as customsfile:

                try:
                    customdict[str(ctx.guild.id)]["prefix"] = prefix
                except KeyError:
                    customdict[str(ctx.guild.id)] = {}
                    customdict[str(ctx.guild.id)]["prefix"] = prefix

                json.dump(customdict, customsfile)

        else:
            prefix = self.bot.command_prefix

        embed = prefixembed(ctx, prefix)

        await ctx.channel.send(embed=embed)

    @settings.command(name="channel", aliases=["set_channel", "music_channel", "set_music_channel"])
    @has_permissions(manage_channels=True)
    @guild_only()
    async def settings_channel(self, ctx: Context, channel: TextChannel):
        """
        Set the channel where the user can control the bots music functions
        """
        with open("customs.json", "r") as channelfile:
            customdict: dict = json.load(channelfile)

        embed = channelembed(channel, ctx.author)
        await ctx.channel.send(embed=embed)

        embed = musicembed(self.bot)

        message: Message = await channel.send(embed=embed)
        await channel.edit(topic="This is the iLoCs channel. You can use commands for this famous bot here!")

        try:
            customdict[str(ctx.guild.id)]["channel"] = channel.id
            customdict[str(ctx.guild.id)]["musicmessage"] = message.id
        except KeyError:
            customdict[str(ctx.guild.id)] = {}
            customdict[str(ctx.guild.id)]["channel"] = channel.id
            customdict[str(ctx.guild.id)]["musicmessage"] = message.id

        with open("customs.json", "w") as channelfile:
            json.dump(customdict, channelfile)

        for react in [backreact, togglepausereact, skipreact, stopreact, loopreact, oneloopreact, shufflereact,
                      ejectreact, lyricreact, redheart, blackheart]:
            await message.add_reaction(react)

    @tasks.loop(seconds=5)
    async def presence(self):
        """
        Task to display amount of servers the bot is currently connected to
        """
        try:
            activity: Game = Game(name=f"on {len(self.bot.guilds)} servers")
            await self.bot.change_presence(activity=activity, status=Status.online)
        except AttributeError:
            pass
