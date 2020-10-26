from discord import VoiceChannel, Message, FFmpegPCMAudio, PCMVolumeTransformer, VoiceClient, Embed, Member
from discord.errors import ClientException
from discord.ext.commands import Bot
import pafy
from typing import List

from embedcreator import musicembed, songembed, overviewembed, lyricembed
from random import shuffle
from errors import NoVideoError, BrokenConnectionError
from asyncio import sleep
from utilities import get_rating, get_lyrics, send_warning


class AudioController:
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    def __init__(self, bot: Bot, message: Message, voice: VoiceClient):
        self.bot = bot
        self.message = message
        self.guild = self.message.guild
        self.voice: VoiceClient = voice
        self.tracks: list = []
        self.old_tracks: list = []
        self.current = None  # Aktueller Track
        self.channel: VoiceChannel = voice.channel
        self.trackindex = 0
        self.repeat: bool = False
        self.onerepeat: bool = False
        self.lyrics_shown: bool = False
        self.skipper: bool = False
        self.goback: bool = False
        self.breaker: bool = False

    def isplaying(self):
        if self.voice.is_playing():
            return True
        else:
            return False

    def ispaused(self) -> bool:
        if self.voice.is_paused():
            return True
        else:
            return False

    def islooping(self) -> bool:
        if self.repeat:
            return True
        elif self.onerepeat:
            return True
        else:
            return False

    def connected_users(self) -> List[Member]:
        return self.channel.members

    async def play(self):
        while self.tracks and len(self.connected_users()) > 1:

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

            await self.display_normal()

            audio = song.getbestaudio()
            try:
                audio.url
            except AttributeError:
                raise NoVideoError
            source = FFmpegPCMAudio(audio.url, **self.FFMPEG_OPTIONS)
            source = PCMVolumeTransformer(source)
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
                elif self.goback:
                    pos = self.tracks.index(self.current)
                    old_track = self.old_tracks[len(self.old_tracks)-1]
                    self.tracks = self.tracks[0:pos] + [old_track] + self.tracks[pos:len(self.tracks)]
                    self.old_tracks.remove(old_track)
                    self.voice.stop()
                    break

            if self.onerepeat:
                continue
            elif self.repeat:
                self.trackindex += 1
            else:
                if self.goback:
                    self.goback = False
                    continue

                try:
                    self.tracks.remove(track)
                    self.old_tracks.append(track)
                except ValueError:
                    pass
                continue

        await self.stop()
        return

    async def pause(self):
        if self.isplaying():
            self.voice.pause()

            self.lyrics_shown = False
            embed = songembed(self.current, self.channel, self.islooping(), self.ispaused())
            await self.message.edit(embed=embed)

    async def resume(self):
        if self.ispaused():
            self.voice.resume()
            await self.display_normal()

    async def skip(self) -> bool:
        if len(self.tracks) > 1:
            self.skipper = True
            return True
        else:
            return False

    async def back(self) -> bool:
        if self.old_tracks:
            self.goback = True
            return True

        else:
            return False

    async def loop(self):
        """
        Let the bot repeat the current track
        """
        if not self.repeat:
            self.repeat = True
        else:
            self.repeat = False

        self.onerepeat = False
        self.lyrics_shown = False

        embed = songembed(self.current, self.channel, self.islooping(), self.ispaused())
        await self.message.edit(embed=embed)

    async def oneloop(self):
        if not self.onerepeat:
            self.onerepeat = True
        else:
            self.onerepeat = False

        self.repeat = False
        self.lyrics_shown = False

        embed = songembed(self.current, self.channel, self.islooping(), self.ispaused())
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
        self.lyrics_shown = False

        embed = overviewembed(self.tracks, self.current, self.bot)
        await self.message.edit(embed=embed)

        await sleep(len(self.tracks) * 3)  # 3 Sekunden pro track

        await self.display_normal()

    async def display_lyrics(self):
        self.lyrics_shown = True

        await send_warning(self.message.channel, "```This may take a few seconds...```")

        lyrics, url = get_lyrics(self.current.request_term)

        embed = lyricembed(self.current, lyrics, url)

        await self.message.edit(embed=embed)

    async def display_normal(self):
        self.lyrics_shown = False

        embed = songembed(self.current, self.channel, self.islooping(), self.ispaused())
        await self.message.edit(embed=embed)

    async def add_to_queue(self, song, requester, term):
        video = Track(song, requester, term)
        self.tracks.append(video)

    async def remove_from_queue(self, track):
        self.tracks.remove(track)
        if track == self.current:
            await self.skip()


class Track:
    def __init__(self, song_url: str, requester: Member, request_term: str):
        while True:
            try:
                self.song = pafy.new(song_url)
            except OSError:
                pass
            else:
                break
        self.requester = requester
        self.request_term = request_term
        self.rating = get_rating(song_url)
