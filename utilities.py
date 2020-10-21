from discord import Message, TextChannel, Embed
from discord.ext.commands import Bot
from discord.errors import NotFound
import json
from data import default_prefix
from apikeys import GOOGLEKEY, GENIUSKEY
from googleapiclient import discovery
from asyncio import sleep
import requests
from collections import namedtuple
from bs4 import BeautifulSoup


API_NAME = "youtube"
API_VERSION = "v3"

YOUTUBE = discovery.build(API_NAME, API_VERSION, developerKey=GOOGLEKEY)


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
    req = YOUTUBE.search().list(q=title, part='snippet', type='video', maxResults=1, pageToken=None)
    res = req.execute()
    video_id = res["items"][0]["id"]["videoId"]
    return f"https://youtube.com/watch?v={video_id}"


async def get_title(term: str):
    req = YOUTUBE.search().list(q=term, part='snippet', type='video', maxResults=1, pageToken=None)
    res = req.execute()
    video_title = res["items"][0]["snippet"]["title"]

    return video_title


async def get_video_list(title: str):
    req = YOUTUBE.search().list(q=title, part='snippet', type='video', maxResults=10, pageToken=None)
    res = req.execute()

    titlelist = namedtuple("titles", ["titles", "creators", "urls"])

    titles = [item["snippet"]["title"] for item in res["items"]]
    creators = [item["snippet"]["channelTitle"] for item in res["items"]]
    urls = ["https://youtube.com/watch?v=" + item["id"]["videoId"] for item in res["items"]]

    data = titlelist(titles, creators, urls)

    return data


async def send_warning(channel: TextChannel, message: str):
    delmessage = await channel.send(message)
    await sleep(7)
    try:
        await delmessage.delete()
    except NotFound:
        pass


async def send_warning_embed(channel: TextChannel, embed: Embed):
    delmessage = await channel.send(embed=embed)
    await sleep(7)
    try:
        await delmessage.delete()
    except NotFound:
        pass


def load_dict():
    try:
        with open("customs.json", "r") as customsfile:
            customdict = json.load(customsfile)
            return customdict

    except FileNotFoundError:
        return {}


def load_favourites(user_id: int):
    try:
        with open("favourites.json", "r") as customsfile:
            try:
                favouritesdict = json.load(customsfile)
                favourites = favouritesdict[str(user_id)]
            except Exception as e:
                print(e)
                favourites = []
            return favourites

    except FileNotFoundError:
        return []


async def save_favourites(user_id: int, favourites: list):
    try:
        with open("favourites.json", "r") as customsfile:
            try:
                favouritedict = json.load(customsfile)
            except json.decoder.JSONDecodeError:
                favouritedict = {}

    except FileNotFoundError:
        favouritedict = {}

    favouritedict[str(user_id)] = favourites

    with open("favourites.json", "w") as customsfile:
        json.dump(favouritedict, customsfile)


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


def get_lyrics(title: str):
    title = title.replace(" ", "%20")

    url = f"https://api.genius.com/search?q={title}&access_token={GENIUSKEY}"

    res = requests.get(url=url)

    try:
        song_id = res.json()["response"]["hits"][0]["result"]["api_path"]
    except IndexError:
        print(res.json())
        return "No Lyrics provided for this song, but that is not my fault!", "https://genius.com"

    url = f"https://api.genius.com{song_id}?access_token={GENIUSKEY}"

    res = requests.get(url)

    lyrics_url = "https://genius.com" + res.json()["response"]["song"]["path"]

    while True:
        try:
            res = requests.get(url=lyrics_url)

            soup = BeautifulSoup(res.text, "html.parser")

            classes = soup.find('div', class_="lyrics")
            lyrics = classes.get_text()
            break
        except AttributeError:
            pass

    return lyrics, lyrics_url


def register_cogs(bot: Bot, cogs: list):
    for cog in cogs:
        bot.add_cog(cog(bot))


if __name__ == '__main__':
    print(get_lyrics("avicii sos"))
