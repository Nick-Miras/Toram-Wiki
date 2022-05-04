from typing import Optional, Sequence, Union, TypedDict

import discord
from discord import Embed
from pydantic import BaseModel as PydanticBaseModel


class SendData(PydanticBaseModel):
    content: Optional[str] = None
    embed: Optional[Embed] = None
    embeds: Optional[list[Embed]] = None
    tts: bool = False
    file: Optional[discord.File] = None
    files: Optional[list[discord.File]] = None
    stickers: Optional[Sequence[Union[discord.GuildSticker, discord.StickerItem]]] = None
    delete_after: Optional[float] = None
    nonce: Optional[int] = None
    allowed_mentions: Optional[discord.AllowedMentions] = None
    reference: Optional[Union[discord.Message, discord.MessageReference, discord.PartialMessage]] = None
    mention_author: Optional[bool] = None
    view: Optional[discord.ui.View] = None

    class Config:
        smart_union = True
        arbitrary_types_allowed = True


class ContentData(TypedDict):
    content: Optional[str]
    embed: Optional[Embed]
