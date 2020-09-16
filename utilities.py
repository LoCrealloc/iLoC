from discord import Message, TextChannel
from discord.ext.commands import Bot
import json
from data import default_prefix
from apikeys import google_key
from googleapiclient import discovery
from asyncio import sleep
import requests
from collections import namedtuple


API_NAME = "youtube"
API_VERSION = "v3"


async def get_custom_prefix(client: Bot, message: Message):
    guild = message.guild
    if guild:
        try:
            with open("customs.json", "r") as customsfile:
                try:
                    customdict: dict = json.load(customsfile)
                except Exception as e:
                    customsfile.close()

                    print(e)
                    customdict = {str(guild.id): {"prefix": ">"}}

                    with open("customs.json", "w") as customfile:
                        json.dump(customdict, customfile)

                    return default_prefix

                try:
                    prefix = customdict[str(guild.id)]["prefix"]
                    return prefix
                except KeyError:
                    return default_prefix
        except FileNotFoundError:
            with open("customs.json", "w") as customsfile:
                json.dump({}, customsfile)

            return default_prefix
    else:
        return default_prefix


async def get_url(title: str):
    youtube = discovery.build(API_NAME, API_VERSION, developerKey=google_key)
    req = youtube.search().list(q=title, part='snippet', type='video', maxResults=1, pageToken=None)
    res = req.execute()
    video_id = res["items"][0]["id"]["videoId"]
    return f"https://youtube.com/watch?v={video_id}"


async def get_video_list(title: str):
    youtube = discovery.build(API_NAME, API_VERSION, developerKey=google_key)
    req = youtube.search().list(q=title, part='snippet', type='video', maxResults=10, pageToken=None)
    res = req.execute()

    titlelist = namedtuple("titles", ["titles", "creators", "urls"])

    titles = [item["snippet"]["title"] for item in res["items"]]
    creators = [item["snippet"]["channelTitle"] for item in res["items"]]
    urls = ["https://youtube.com/watch?v=" + item["id"]["videoId"] for item in res["items"]]

    data = titlelist(titles, creators, urls)

    return data


async def send_warning(channel: TextChannel, message: str):
    delmessage = await channel.send(message)
    await sleep(5)
    await delmessage.delete()


def get_rating(video_url):
    rating = namedtuple("Rating", ["likes", "dislikes"])

    res = requests.get(url=video_url)

    plain = res.text

    likes = plain.split('{"iconType":"LIKE"},"defaultText":{"accessibility":{"accessibilityData":'
                              '{"label":"')[1].split(' \\"')[0]

    dislikes = plain.split('{"iconType":"DISLIKE"},"defaultText":{"accessibility":{"accessibilityData":'
                                 '{"label":"')[1].split("\xa0")[0]

    data = rating(likes, dislikes)

    return data


def register_cogs(bot: Bot, cogs: list):
    for cog in cogs:
        bot.add_cog(cog(bot))
