from discord.ext.commands import Bot, Context
from discord import Embed, TextChannel, Member
from data import color, manual_url, version, features, loc_mention


async def infoembed(bot: Bot, message):
    embed = Embed(title="iLoC",
                  description="The most advanced Discord music bot",
                  color=color,
                  url=manual_url)
    embed.set_thumbnail(url=bot.user.avatar_url)
    embed.add_field(name="Features", value="\n".join(f"- {feature}" for feature in features), inline=False)
    embed.add_field(name="Version", value=version, inline=True)
    embed.add_field(name="Manual", value=manual_url, inline=True)
    embed.add_field(name="Help-Command", value=f"{await bot.command_prefix(bot, message)}help", inline=False)
    embed.add_field(name="Developer", value=f"This Discord bot is developed by {loc_mention}! Please tell me any "
                                             f"issues on GitHub or via DM", inline=False)

    return embed


def prefixembed(ctx: Context, prefix: str):
    embed = Embed(title="Prefix changed",
                  description="The prefix for the iLoC has been changed",
                  color=color)

    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

    embed.add_field(name="New Prefix", value=prefix)

    return embed


def channelembed(channel: TextChannel, author: Member):
    embed = Embed(title="Channel changed",
                  description="The channel where you can control the bot's msuic functions has been changed",
                  color=color)

    embed.set_author(name=author.display_name, icon_url=author.avatar_url)

    embed.add_field(name="New Channel", value=channel.name, inline=False)

    return embed


def listembed(member: Member, search: str, titles: list, creators: list):
    embed = Embed(title="Search result",
                  description=f"The results for {member.mention}'s search for {search}",
                  color=color)

    embed.set_author(name=member.display_name, url=member.avatar_url)

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


def songembed(bot: Bot, track, channel, loop, paused):
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
