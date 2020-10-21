from discord.ext.commands import Bot, Context
from discord import Embed, TextChannel, Member, Invite
from data import color, repository_url, version, features, loc_mention
from textwrap import TextWrapper


async def infoembed(bot: Bot, message):
    embed = Embed(title="iLoC",
                  description="The most advanced Discord music bot",
                  color=color,
                  url=repository_url)
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.add_field(name="Features", value="\n".join(f"- {feature}" for feature in features), inline=False)
    embed.add_field(name="Version", value=version, inline=True)
    embed.add_field(name="GitHub", value=repository_url, inline=True)
    embed.add_field(name="Help-Command", value=f"{await bot.command_prefix(bot, message)}help", inline=False)
    embed.add_field(name="Developer", value=f"This Discord bot is developed by {loc_mention}! Please tell me any "
                                             f"issues on GitHub or via DM", inline=False)

    return embed


def settingsembed(bot: Bot, prefix: str):
    embed = Embed(title="Settings",
                  description="You can edit the bots preferences by using the commands below!",
                  color=color)
    embed.set_author(name=bot.user.display_name, icon_url=bot.user.avatar_url)
    embed.add_field(name=f"{prefix}settings prefix", value="Change the bots prefix")
    embed.add_field(name=f"{prefix}settings channel", value="Set the channel where to control the bot!")
    embed.set_footer(text=repository_url)

    return embed


def prefixembed(ctx: Context, prefix: str):
    embed = Embed(title="Prefix changed",
                  description="The prefix for the iLoC has been changed",
                  color=color)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="New Prefix", value=prefix)

    return embed


def notinchannelembed(author: Member, invite: Invite):
    embed = Embed(title="Please connect to the bots channel",
                  description="The bot is connected to a channel you are not connected to! "
                              "Please connect to this channel to control the bot!",
                  color=color)

    embed.set_author(name=author.display_name, icon_url=author.avatar_url)

    embed.add_field(name="Invite", value=invite.url)

    return embed


def channelembed(channel: TextChannel, author: Member):
    embed = Embed(title="Channel changed",
                  description="The channel where you can control the bots music functions has been changed",
                  color=color)

    embed.set_author(name=author.display_name, icon_url=author.avatar_url)

    embed.add_field(name="New Channel", value=channel.name, inline=False)

    return embed


def listembed(member: Member, search: str, titles: list, creators: list):
    embed = Embed(title="Search result",
                  description=f"The results for {member.mention}'s search for {search}",
                  color=color)

    embed.set_author(name=member.display_name, icon_url=member.avatar_url)

    for i in range(len(titles)):
        title = titles[i]
        creator = creators[i]
        embed.add_field(name=f"{i + 1}: {title}", value=f"Creator: {creator}")

    embed.set_footer(text="Send the song's number in this channel to select the song you want to play!")

    return embed


def musicembed(bot: Bot):
    embed = Embed(title="iLoC",
                  description="Play music in this channel using the *play*-command! You can pause, resume, skip, loop, "
                              "shuffle and stop the music using the reactions below this message! Have fun!",
                  color=color)

    embed.set_author(name=bot.user.display_name, icon_url=bot.user.avatar_url)

    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.add_field(name="Current channel", value="None", inline=True)
    embed.add_field(name="Loop", value="Disabled", inline=True)
    embed.add_field(name="Paused", value="No", inline=True)
    embed.add_field(name="Current song", value="None", inline=True)
    embed.add_field(name="Creator", value="None", inline=True)
    embed.add_field(name="Length", value="None", inline=True)
    embed.add_field(name="Views", value="None", inline=True)
    embed.add_field(name="Likes", value="None", inline=True)
    embed.add_field(name="Dislikes", value="None", inline=True)

    embed.set_footer(text="The most advanced music bot")

    return embed


def songembed(track, channel, loop, paused):
    video = track.song
    rating = track.rating
    requester: Member = track.requester

    embed = Embed(title="iLoC",
                  description="Play music in this channel using the *play*-command! You can pause, resume, skip, loop, "
                              "shuffle and stop the music using the reactions below this message! Have fun!",
                  color=color)

    embed.set_author(name=requester.display_name, icon_url=requester.avatar_url)

    embed.set_thumbnail(url=video.thumb)
    embed.add_field(name="Current channel", value=channel, inline=True)
    embed.add_field(name="Loop", value="Enabled" if loop else "Disabled", inline=True)
    embed.add_field(name="Paused", value="Yes" if paused else "No", inline=True)
    embed.add_field(name="Current song", value=video.title, inline=True)
    embed.add_field(name="Creator", value=video.author, inline=True)
    embed.add_field(name="Length", value=f"{video.length} seconds", inline=True)
    embed.add_field(name="Views", value=video.viewcount, inline=True)
    embed.add_field(name="Likes", value=f"{rating.likes} 👍", inline=True)
    embed.add_field(name="Dislikes", value=f"{rating.dislikes} 👎", inline=True)

    embed.set_footer(text="The most advanced music bot")

    return embed


def overviewembed(songs: list, current, bot: Bot):
    titlelist = [song.song.title for song in songs]

    embed = Embed(title="Songs in queue",
                  description="Here you can see what songs are currently in your queue! "
                              "Play a song using the *play {song}*-command!",
                  color=color)
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.add_field(name="Queue", value="\n".join(["- " + title for title in titlelist]))
    embed.add_field(name="Current song", value=f"{current.song.title}")
    embed.add_field(name="Place in queue", value=f"{titlelist.index(current.song.title) + 1}")

    return embed


def lyricembed(track, lyrics: str, lyric_url: str):
    video = track.song
    requester: Member = track.requester

    wrapper = TextWrapper(width=2040, replace_whitespace=False, placeholder="[...]")

    newlyrics = wrapper.wrap(lyrics)[0]

    embed = Embed(title=f"Lyrics for {video.title}",
                  url=lyric_url,
                  description=newlyrics if len(lyrics) <= 2048 else newlyrics + "\n[...]",
                  color=color)

    embed.set_author(name=requester.display_name, icon_url=requester.avatar_url)
    embed.set_thumbnail(url=video.thumb)
    embed.set_footer(text="Lyrics provided by https://genius.com")

    return embed


def playlistembed(favourites: list, user: Member):
    embed = Embed(title=f"Playlist for {user.display_name}",
                  description=f"You have saved {len(favourites)} "
                              f"{'songs' if len(favourites) > 1 or len(favourites) == 0 else 'song'} "
                              f"to your playlist!",
                  color=color)

    embed.set_author(name=user.display_name, icon_url=user.avatar_url)

    for song in favourites:
        embed.add_field(name=f"Song #{favourites.index(song) + 1}", value=song, inline=False)

    embed.set_footer(text="You can add 5 Songs to your playlist!")

    return embed
