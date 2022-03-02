import discord
from discord.ext.commands import CommandError


class Error(CommandError):
    def __init__(self, message, embed: bool = False, channel=None):
        """Custom Error Command that can be handled by the Error Cogs.

        Parameters
        ----------
        message:
            This is the message to be sent by the bot to the user
        embed: :class: `bool`
            Defaults to `False` if True then it will send the message with an
        channel: :class: `discord.abc.Messageable`
            The message-able that the message will be sent to
        """
        self.message = message

        if not isinstance(channel, discord.abc.Messageable):
            # If channel is not message-able then use `discord.ext.command.Context` instead
            self.channel = None
        else:
            self.channel = channel

        if isinstance(message, discord.Embed):
            # If the message is an embed then disable the embed feature for preventing errors
            self.use_embed = False
            message = message.description
        else:
            self.use_embed = embed

        super().__init__(message)