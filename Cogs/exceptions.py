from typing import Optional

import discord
from discord.ext.commands import CommandError


class CmdError(CommandError):
    def __init__(
            self,
            message: str | discord.Embed,
            should_use_embed: bool = False,
            channel: Optional[discord.abc.Messageable] = None
    ):
        """Custom Error Command that can be handled by the Error Cogs.

        Parameters
        ----------
        message:
            This is the message to be sent by the bot to the user
        should_use_embed: :class: `bool`
            Defaults to `False` if True then it will send the message with an
        channel: :class: `discord.abc.Messageable`
            The message-able that the message will be sent to
        """
        self.should_use_embed = should_use_embed
        self.message = message
        self.channel = channel

        if isinstance(message, discord.Embed):
            # If the message is an embed then disable the embed feature for preventing errors
            self.should_use_embed = False
            message = message.description

        super().__init__(message)
