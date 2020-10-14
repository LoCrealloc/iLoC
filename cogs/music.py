from discord.ext.commands import Cog, command, Bot, Context, guild_only, check, group
from discord import Message, TextChannel, VoiceClient, RawReactionActionEvent, VoiceState, Member, Reaction
from utilities import get_url, get_video_list, send_warning
import json
from data import togglepausereact, stopreact, skipreact, backreact, loopreact, oneloopreact, \
                 shufflereact, ejectreact, lyricreact, blackheart, redheart, num_reacts, num_meanings
from audio import AudioController
from errors import NoVideoError, BrokenConnectionError, WronReactError
from embedcreator import listembed, playlistembed
from asyncio import TimeoutError
from utilities import save_favourites, load_favourites, get_title


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
            except AttributeError:
                return True

    except FileNotFoundError:
        print("NoFileError")
        return False

    if playchannel_id == ctx.channel.id:
        return True
    else:
        await ctx.message.delete()
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
            try:
                voice = await ctx.author.voice.channel.connect()
            except AttributeError:
                await send_warning(ctx.channel, "```You are not connected to a voice channel!```")
                return

        playchannel: TextChannel = ctx.channel
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
            controller = AudioController(self.bot, message, voice)
            self.controllers[str(ctx.guild.id)] = controller

        for song in songs:
            url = await get_url(song)
            await controller.add_to_queue(url, ctx.author, song)

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
    async def search(self, ctx: Context, *song):
        """
        Lets you search and play a song on youtube
        """

        song = " ".join(song)

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
            num = num_meanings[str(reaction.emoji)]  # Getted die Position des ausgewählten songs aus nem Dict
            await message.delete()

        num -= 1  # Für Listen, muss verbessert werden!

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

    @group(name="playlist", aliases=["pl", "tracklist", "favourites"])
    async def playlist(self, ctx: Context):
        """
        Add songs to your playlist with playlist add (songs) or by  reacting with a heart when they are currently played
        """

    @playlist.command(name="show", aliases=["display"])
    async def playlist_show(self, ctx: Context):
        """
        Watch the tracks you have saved to your playlist
        """
        favourites = load_favourites(ctx.author.id)
        embed = playlistembed(favourites, ctx.author)
        await ctx.author.send(embed=embed)

    @playlist.command(name="clear", aliases=["delete"])
    async def playlist_clear(self, ctx: Context):
        """
        Removes all songs from your playlist
        """
        await save_favourites(ctx.author.id, [])
        await ctx.author.send("All songs have been cleared from your playlist ✅")

    @playlist.command(name="add", alisases=["append"])
    async def playlist_add(self, ctx: Context):
        favourites = load_favourites(ctx.author.id)
        bot_prefix = await self.bot.command_prefix(self.bot, ctx.message)

        try:
            parts = ctx.message.content.split(f"{bot_prefix}playlist add ")
            songs = parts[1].split(",")
        except IndexError:
            await send_warning(ctx.channel, "```You must specify at least one song!```")
            return

        if len(songs + favourites) <= 5:
            song_videos = []
            for song in songs:
                song_videos.append(await get_title(song))

            await save_favourites(ctx.author.id, favourites + song_videos)

            await ctx.author.send(f"Added {len(songs)} {'songs' if len(favourites) > 1 else 'song'} to your playlist ✅")

        else:
            await ctx.author.send("You can only save 5 songs to your playlist, sorry!")

    @playlist.command(name="play", aliases=["start"])
    @guild_only()
    async def playlist_play(self, ctx: Context):
        favourites = load_favourites(ctx.author.id)

        await send_warning(ctx.channel, f"```{len(favourites)} "
                                        f"{'songs' if len(favourites) > 1 or len(favourites) == 0 else 'song'} "
                                        f"were added to the queue!```")

        await self.play_songs(ctx, favourites)

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

                if reaction.member in controller.connected_users():
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

                    elif reaction.emoji.name == backreact:
                        if not await controller.back():
                            await send_warning(message.channel, "```There is no song played before!```")

                    elif reaction.emoji.name == loopreact:
                        await controller.loop()

                    elif reaction.emoji.name == oneloopreact:
                        await controller.oneloop()

                    elif reaction.emoji.name == shufflereact:
                        await controller.shuffle()

                    elif reaction.emoji.name == ejectreact:
                        await controller.remove_from_queue(controller.current)

                    elif reaction.emoji.name == lyricreact:
                        if not controller.lyrics_shown:
                            await controller.display_lyrics()
                        else:
                            await controller.display_normal()

                    elif reaction.emoji.name == redheart:

                        favourites: list = load_favourites(reaction.member.id)
                        song_title = controller.current.song.title

                        if song_title not in favourites:
                            if len(favourites) < 5:
                                favourites.append(song_title)
                                await save_favourites(reaction.member.id, favourites)
                                await send_warning(self.bot.get_channel(reaction.channel_id), "✅")

                            else:
                                await send_warning(self.bot.get_channel(reaction.channel_id),
                                                   "```You can only save 5 songs to your playlist, sorry!```")
                        else:
                            await send_warning(self.bot.get_channel(reaction.channel_id),
                                               "```You have already given this song in your playlist!```")

                    elif reaction.emoji.name == blackheart:
                        favourites = load_favourites(reaction.member.id)
                        song_title = controller.current.song.title

                        if song_title in favourites:
                            favourites.remove(song_title)
                            await save_favourites(reaction.member.id, favourites)
                            await send_warning(self.bot.get_channel(reaction.channel_id), "✅")
                        else:
                            await send_warning(self.bot.get_channel(reaction.channel_id),
                                               "```This song is not saved in your playlist yet!```")

                else:
                    await send_warning(self.bot.get_channel(reaction.channel_id),
                                       f"```You have to be connected to the voice channel the bot is "
                                       f"connected to ({controller.channel})```")

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member == self.bot.user:
            if after.channel is None:
                guild_id = before.channel.guild.id
                controller = self.controllers[str(guild_id)]
                del controller
                del self.controllers[str(guild_id)]
