from discord import Guild, VoiceChannel, Message, FFmpegPCMAudio, VoiceClient, Embed, Member
from discord.errors import ClientException
from discord.ext.commands import Bot
import pafy
from embedcreator import musicembed, songembed, overviewembed
from random import shuffle
from errors import NoVideoError, BrokenConnectionError
from asyncio import sleep
from utilities import get_rating


class AudioController:
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, bot: Bot, guild: Guild, message: Message, voice: VoiceClient):
        self.bot = bot
        self.guild = guild
        self.message = message
        self.voice: VoiceClient = voice
        self.tracks: list = []
        self.current = None  # Aktueller Track
        self.channel: VoiceChannel = voice.channel
        self.trackindex = 0
        self.repeat: bool = False
        self.skipper: bool = False
        self.breaker: bool = False

    def isplaying(self):
        if self.voice.is_playing():
            return True
        else:
            return False

    def ispaused(self):
        if self.voice.is_paused():
            return True
        else:
            return False

    def connected_users(self):
        return self.channel.members

    async def play(self):
        while self.tracks:

            try:
                track = self.tracks[self.trackindex]
                song = track.song

                self.current = track

            except IndexError:
                if not self.repeat:
                    await self.stop()
                    return
                else:
                    self.trackindex = 0
                    continue

            embed: Embed = songembed(self.bot, track, self.channel, self.repeat, self.ispaused())

            await self.message.edit(embed=embed)

            audio = song.getbestaudio()
            try:
                audio_url = audio.url
            except AttributeError:
                raise NoVideoError
            source = FFmpegPCMAudio(audio_url, **self.FFMPEG_OPTIONS)
            try:
                self.voice.play(source)
            except ClientException:
                raise BrokenConnectionError

            while self.isplaying() or self.ispaused():
                await sleep(1)
                if self.skipper:
                    self.skipper = False
                    self.voice.stop()
                    break
                elif self.breaker:
                    return

            if not self.repeat:
                self.tracks.remove(track)
            else:
                self.trackindex += 1

        await self.stop()
        return

    async def pause(self):
        if self.isplaying():
            self.voice.pause()

            embed = songembed(self.bot, self.current.song, self.channel, self.repeat, self.ispaused())
            await self.message.edit(embed=embed)

    async def resume(self):
        if self.ispaused():
            self.voice.resume()
            embed = songembed(self.bot, self.current.song, self.channel, self.repeat, self.ispaused())
            await self.message.edit(embed=embed)

    async def skip(self):
        if len(self.tracks) > 0:
            self.skipper = True
            return True
        else:
            return False

    async def loop(self):
        """
        Lässt den Bot die aktuelle Playlist wiederholen
        """
        if not self.repeat:
            self.repeat = True
        else:
            self.repeat = False

        embed = songembed(self.bot, self.current.song, self.channel, self.repeat, self.ispaused())
        await self.message.edit(embed=embed)

    async def shuffle(self):
        shuffle(self.tracks)

    async def stop(self):
        self.breaker = True
        self.voice.stop()
        await self.voice.disconnect()
        embed: Embed = musicembed(self.bot)
        await self.message.edit(embed=embed)

    async def display_queue(self):
        embed = overviewembed(self.tracks, self.current.song, self.bot)
        await self.message.edit(embed=embed)

        await sleep(len(self.tracks) * 3)  # 3 Sekunden pro track

        embed = songembed(self.bot, self.current.song, self.channel, self.repeat, self.ispaused())
        await self.message.edit(embed=embed)

    async def add_to_queue(self, song, requester):
        video = Track(song, requester)
        self.tracks.append(video)

    async def remove_from_queue(self, track):
        self.tracks.remove(track)
        if track == self.current:
            await self.skip()


class Track:
    def __init__(self, song_url: str, requester: Member):
        self.song = pafy.new(song_url)
        self.requester = requester
        self.rating = get_rating(song_url)
