import json
from discord.ext.commands import Bot, errors, Context
from apikeys import TOKEN
from data import joinmessage
from discord import Message, Guild
from cogs.information import Information
from cogs.settings import Settings
from cogs.music import Music
from utilities import get_custom_prefix, register_cogs, send_warning
from errors import WrongChannelError, NotConnectedError


bot = Bot(command_prefix=get_custom_prefix, case_insensitive=True)


@bot.event
async def on_ready():
    print(f"Bot has logged in as {bot.user.display_name} successfully!")


@bot.event
async def on_message(message: Message):

    if not message.author == bot.user:

        try:
            with open("customs.json", "r") as customsfile:
                customdict = json.load(customsfile)

            try:
                playchannel_id = customdict[str(message.guild.id)]["channel"]

                if message.channel.id == playchannel_id:

                    await message.delete()

                    prefix = str(await bot.command_prefix(bot, message))

                    if message.content.startswith(prefix + "help") or message.content.startswith(prefix + "settings"):

                        await send_warning(message.channel, "Please use another channel for the help or settings "
                                                            "command!")
                        return

            except KeyError:
                print("KeyError")

            except AttributeError:
                pass

        except FileNotFoundError:
            print("NoFileError")

        await bot.process_commands(message)


@bot.event
async def on_guild_join(guild: Guild):
    if guild.system_channel:
        await guild.system_channel.send(content=joinmessage)
    else:
        channel = guild.text_channels[0]
        await channel.send(joinmessage)

    try:
        with open("guilds.json", "r") as guildfile:
            guilds: list = json.load(guildfile)["guilds"]
            guilds.append(guild.id)

        with open("guilds.json", "w") as guildfile:
            guilddict = {"guilds": guilds}
            json.dump(guilddict, guildfile)

    except FileNotFoundError:
        with open("guilds.json", "w") as guildfile:
            guilddict = {"guilds": [guild.id]}
            json.dump(guilddict, guildfile)


@bot.event
async def on_guild_remove(guild: Guild):
    try:
        with open("guilds.json", "r") as guildfile:
            guilds: list = json.load(guildfile)["guilds"]
            guilds.remove(guild.id)

        with open("guilds.json", "w") as guildfile:
            guilddict = {"guilds": guilds}
            json.dump(guilddict, guildfile)

    except FileNotFoundError:
        with open("guilds.json", "w") as guildfile:
            guilddict = {"guilds": []}
            json.dump(guilddict, guildfile)


@bot.event
async def on_command_error(ctx: Context, error: errors.CommandError):
    if isinstance(error, errors.MissingRequiredArgument):
        await ctx.channel.send("There are parameters missing for this command!")

    elif isinstance(error, errors.BadArgument):
        await ctx.channel.send("Your parameter's value was invalid!")

    elif isinstance(error, errors.MissingPermissions):
        await ctx.channel.send("You have no permission to use this command")

    elif isinstance(error, errors.CommandNotFound):
        await ctx.channel.send("This command doesn't exist!")

    elif isinstance(error, NotConnectedError):
        await send_warning(ctx.channel, "```You have to be connected to a voice channel to use this command!```")

    elif isinstance(error, WrongChannelError):
        await send_warning(ctx.channel, f"```Please use only the music channel specified for this "
                                        f"server for music commands! Set a music channel using "
                                        f"{await bot.command_prefix(bot, ctx.message)}channel [channel]!```")
    
    elif isinstance(error, errors.CheckFailure):
        await send_warning(ctx.channel, f"Other check failure: {error}")
    
    elif isinstance(error, errors.NoPrivateMessage):
        await ctx.author.send("This command cannot be used in direct messages!")

    else:
        print(error)
        await ctx.channel.send(f"ERROR! For an overview, type {await bot.command_prefix(bot, ctx.message)}help!")


register_cogs(bot, [Information, Settings, Music])

bot.run(TOKEN)
