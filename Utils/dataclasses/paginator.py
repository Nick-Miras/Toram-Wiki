from enum import Enum
from typing import Optional

import discord
from bson import ObjectId
from pydantic import Field

from Utils.dataclasses.abc import WikiBaseModel


class PageType(Enum):
    HELP = 'help'


class InformationPage(WikiBaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias='_id')
    parent: Optional[ObjectId] = None
    embed: discord.Embed
