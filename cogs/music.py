from discord.ext.commands import Cog, command, Bot, Context, guild_only, check
from discord import Message, TextChannel, VoiceClient, RawReactionActionEvent, VoiceState, Member, Reaction
from utilities import get_url, get_video_list, send_warning
import json
from data import togglepausereact, stopreact, skipreact, loopreact, shufflereact, ejectreact, \
                 num_reacts, num_meanings
from audio import AudioController
from errors import NoVideoError, BrokenConnectionError, WronReactError
from embedcreator import listembed
from asyncio import TimeoutError


@check
async def check_channel(ctx: Context):
    """
    Function to check whether the channel used for the command is the music channel set for the guild
    """

    try:
        with open("customs.json", "r") as customsfile:
            customdict = json.load(customsfile)

            try:
                playchannel_id = customdict[str(ctx.guild.id)]["channel"]

            except KeyError:
                return False

    except FileNotFoundError:
        print("NoFileError")
        return False

    if playchannel_id == ctx.channel.id:
        return True
    else:
        return False


@check
async def is_connected(ctx: Context):
    """
    Function to check whether a user is currently connected to a voice channel
    """

    return True if ctx.author.voice else False


class Music(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.controllers = {}

    async def play_songs(self, ctx: Context, songs):
        try:
            # Checkt, ob der Bot auf dem Server schon in einem Sprachkanal ist

            voice: VoiceClient = [client if client.guild.id == ctx.guild.id else None
                                  for client in self.bot.voice_clients][0]

            if not voice.channel == ctx.author.voice.channel:
                await send_warning(ctx.channel, "```The bot is already connected to a channel you are not "
                                                "connected to!```")
                return

        except IndexError:
            # Der Bot tritt einem Kanal bei, falls er noch mit keinem verbunden ist
            voice = await ctx.author.voice.channel.connect()

        playchannel: TextChannel = self.bot.get_channel(ctx.channel.id)
        # playchannel = Der Kanal, der für den Bot festgelegt wurde

        with open("customs.json", "r") as customsfile:
            customdict = json.load(customsfile)

        message: Message = await playchannel.fetch_message(customdict[str(ctx.guild.id)]["musicmessage"])
        # Die Nachricht des Bots, welche das Musik-Embed enthält

        try:
            controller: AudioController = self.controllers[str(ctx.guild.id)]
            # Erhält den AudioController aus dem Dictionary von Controllers
        except KeyError:
            # Wenn kein Audiocontroller -> Audiocontroller wird erstellt
            controller = AudioController(self.bot, ctx.guild, message, voice)
            self.controllers[str(ctx.guild.id)] = controller

        for song in songs:
            song = await get_url(song)
            await controller.add_to_queue(song, ctx.author)

        if not controller.isplaying():
            try:
                await controller.play()
            except NoVideoError:
                await send_warning(ctx.channel, "```No video found! Passing...```")
            except BrokenConnectionError:
                del controller
                try:
                    del self.controllers[str(ctx.guild.id)]
                except KeyError:
                    pass
                return

    @command(name="play", aliases=["p"])
    @guild_only()
    @check_channel
    @is_connected
    async def play(self, ctx: Context):
        """
        Plays a song in the  channel you are connected to! You can specify multiple songs by
        separating them with a comma
        """
        bot_prefix = await self.bot.command_prefix(self.bot, ctx.message)

        try:
            parts = ctx.message.content.split(f"{bot_prefix}play ")
            songs = parts[1].split(",")
        except IndexError:
            await send_warning(ctx.channel, "```You must specify at least one song!```")
            return

        await self.play_songs(ctx, songs)

    @command(name="search")
    @guild_only()
    @check_channel
    @is_connected
    async def search(self, ctx: Context, song: str):
        """
        Lets the user search a song on youtube
        """

        data = await get_video_list(song)

        embed = listembed(ctx.author, song, data.titles, data.creators)

        message: Message = await ctx.channel.send(embed=embed)

        for react in num_reacts:
            await message.add_reaction(react)

        def check_reaction(reaction: Reaction, user):
            if not self.bot.user == user:

                if not str(reaction.emoji) in num_reacts:
                    raise WronReactError
                return reaction.message.id == message.id and user.id == ctx.author.id
            else:
                return False

        try:
            reaction, user = await self.bot.wait_for(event="reaction_add", timeout=30.0, check=check_reaction)
        except TimeoutError:
            await message.delete()
            return
        except Exception as e:
            await message.delete()
            print(e)
            return
        else:
            num = num_meanings[str(reaction.emoji)]  # Getted die Zahl des ausgewählten songs aus nem Dict
            await message.delete()

        num -= 1  # Für Listen

        song = data.urls[num]

        await self.play_songs(ctx, [song])

    @command(name="queue", aliases=["q", "songs", "tracks"])
    @guild_only()
    @check_channel
    async def queue(self, ctx: Context):
        """
        Displays the tracks which are currently in your queue
        """
        try:
            controller: AudioController = self.controllers[str(ctx.guild.id)]
        except KeyError:
            try:
                await ctx.message.delete()
            except Exception as e:
                print(e)
            return

        if ctx.message.channel.id == controller.message.channel.id:
            await controller.display_queue()
        else:
            print(controller.message.id)
            print(ctx.message.id)

            await send_warning(ctx.channel, f"```Please use only the channel specified for this bot "
                                            f"({controller.message.channel.mention}) for music commands```")
            await ctx.message.delete()

    @Cog.listener()
    @guild_only()
    async def on_raw_reaction_add(self, reaction: RawReactionActionEvent):
        if not reaction.member == self.bot.user:

            try:
                with open("customs.json", "r") as customsfile:
                    customdict = json.load(customsfile)

                    try:
                        message_id = customdict[str(reaction.guild_id)]["musicmessage"]

                    except KeyError:
                        return

            except FileNotFoundError:
                print("NoFileError")
                return

            if message_id == reaction.message_id:

                channel: TextChannel = self.bot.get_channel(reaction.channel_id)
                message = await channel.fetch_message(reaction.message_id)

                await message.remove_reaction(reaction.emoji.name, reaction.member)

                try:
                    controller: AudioController = self.controllers[str(reaction.guild_id)]
                except KeyError:
                    return

                if controller.isplaying() or controller.ispaused() and reaction.member in controller.connected_users():
                    if reaction.emoji.name == togglepausereact:
                        if not controller.ispaused():
                            await controller.pause()
                        else:
                            await controller.resume()

                    elif reaction.emoji.name == stopreact:
                        await controller.stop()
                        del controller
                        try:
                            del self.controllers[str(reaction.guild_id)]
                        except KeyError:
                            pass

                    elif reaction.emoji.name == skipreact:
                        if not await controller.skip():
                            await send_warning(message.channel, "```There are no other songs in the queue!```")

                    elif reaction.emoji.name == loopreact:
                        await controller.loop()

                    elif reaction.emoji.name == shufflereact:
                        await controller.shuffle()

                    elif reaction.emoji.name == ejectreact:
                        await controller.remove_from_queue()

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member == self.bot.user:
            if after.channel is None:
                guild_id = before.channel.guild.id
                controller = self.controllers[str(guild_id)]
                del controller
                del self.controllers[str(guild_id)]
