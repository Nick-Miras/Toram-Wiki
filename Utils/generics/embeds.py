from abc import ABC, abstractmethod

import discord

from Utils import ColorVar, Images


class EmbedModel(ABC):

    @staticmethod
    @abstractmethod
    def get(message: str = None) -> discord.Embed:
        ...


class ErrorEmbed(EmbedModel):

    @staticmethod
    def get(message: str = None) -> discord.Embed:
        embed = discord.Embed(
            description=message,
            color=ColorVar.error_red
        )
        embed.set_thumbnail(url=Images.exclamation)
        embed.set_author(name='Error!')
        return embed


class NotificationEmbed(EmbedModel):

    @staticmethod
    def get(message: str = None) -> discord.Embed:
        embed = discord.Embed(
            description=message,
            color=ColorVar.gold
        )
        embed.set_author(name='Notification!')
        embed.set_thumbnail(url=Images.notifications)
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
            color=ColorVar.bright_green
        )
        embed.set_thumbnail(url=Images.successful)
        embed.set_author(name='Success!')
        return embed
