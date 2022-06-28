from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional

import discord
import requests
from discord import Embed
from discord.ext import commands

from Utils.constants import colors
from Utils.constants import images
from Utils.dataclasses.discord import ContentData
from Utils.paginator.page import PaginatorView


def to_message_data(value: str | Embed) -> Optional[ContentData]:
    """transforms the data into a :class:`dict` to be used by :class:`discord.Message`
    """
    if isinstance(value, str):
        return {'content': value, 'embed': ''}
    if isinstance(value, Embed):
        return {'content': '', 'embed': value}


async def send_with_paginator(ctx: commands.Context, paginator: PaginatorView):
    # sends the initial page along with the paginator view
    message_data = paginator.controller.current.get_content()
    return await ctx.send(**message_data, view=paginator)


class _EmbedModels:

    @staticmethod
    def guild_document(guild_id: int) -> dict:
        """
        This function returns the database document for initializing new Discord Servers that were added

        :param guild_id: :class: `int` This is the id of the guild
        """
        assert isinstance(guild_id, int)
        document = {'_id': guild_id,
                    'prefix': '.',
                    'exempted': False
                    }
        return document

    @staticmethod
    def error_embed(message=None):
        """Embed for Error Messages

        Parameters
        -----------
        message: :class: `str`
            The error message to be sent.
        """
        embed = discord.Embed(
            description=message,
            color=colors.ERROR_RED
        )
        embed.set_thumbnail(url=images.EXCLAMATION)
        embed.set_author(name='Error!')
        return embed

    @staticmethod
    def success_embed(message=None):
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

    @staticmethod
    def notification(message=None):
        embed = discord.Embed(
            description=message,
            color=colors.GOLD
        )
        embed.set_author(name='Notification!')
        embed.set_thumbnail(url=images.NOTIFICATIONS)
        return embed


class EmbedModels(ABC):

    @staticmethod
    @abstractmethod
    def display(message: str) -> discord.Embed:
        pass


class NotificationEmbed(EmbedModels):

    @staticmethod
    def display(message: str) -> discord.Embed:
        embed = discord.Embed(
            description=message,
            color=colors.GOLD
        )
        embed.set_author(name='Notification!')
        embed.set_thumbnail(url=images.NOTIFICATIONS)
        return embed


class SuccessEmbed(EmbedModels):

    @staticmethod
    def display(message: str) -> discord.Embed:
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


class ErrorEmbed(EmbedModels):
    @staticmethod
    def display(message: str) -> discord.Embed:
        """Embed for Error Messages

        Parameters
        -----------
        message: :class: `str`
            The error message to be sent.
        """
        embed = discord.Embed(
            description=message,
            color=colors.ERROR_RED
        )
        embed.set_thumbnail(url=images.EXCLAMATION)
        embed.set_author(name='Error!')
        return embed


def get_image_from_link(link: str) -> Optional[discord.File]:
    """
    Returns:
        Optional[discord.File]
    """
    if not link:
        return
    if not link.startswith('http'):
        link = 'http:' + link
    try:
        response = requests.get(link)
        if response.status_code == 200:
            return discord.File(BytesIO(response.content), filename=link.split('/')[-1])
    except Exception:
        return
