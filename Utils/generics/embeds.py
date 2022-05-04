from abc import ABC, abstractmethod

import discord

from Utils.constants import colors, images


class EmbedModel(ABC):

    @staticmethod
    @abstractmethod
    def get(message: str = None) -> discord.Embed:
        pass


class ErrorEmbed(EmbedModel):

    @staticmethod
    def get(message: str = None) -> discord.Embed:
        embed = discord.Embed(
            description=message,
            color=colors.ERROR_RED
        )
        embed.set_thumbnail(url=images.EXCLAMATION)
        embed.set_author(name='Error!')
        return embed


class NotificationEmbed(EmbedModel):

    @staticmethod
    def get(message: str = None) -> discord.Embed:
        embed = discord.Embed(
            description=message,
            color=colors.GOLD
        )
        embed.set_author(name='Notification!')
        embed.set_thumbnail(url=images.NOTIFICATIONS)
        return embed


class SuccessEmbed(EmbedModel):

    @staticmethod
    def get(message: str = None) -> discord.Embed:
        """Embed for Successful Processes or Command Invocations


        Parameters
        -----------
        message: :class: `str`
            The success message to be sent.
        """
        embed = discord.Embed(
            description=message,
            color=colors.BRIGHT_GREEN
        )
        embed.set_thumbnail(url=images.SUCCESSFUL)
        embed.set_author(name='Success!')
        return embed
