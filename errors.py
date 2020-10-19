from discord.ext.commands import CheckFailure


class NoVideoError(Exception):
    pass


class BrokenConnectionError(Exception):
    pass


class WrongReactError(Exception):
    pass


class WrongChannelError(CheckFailure):
    pass


class NotConnectedError(CheckFailure):
    pass
