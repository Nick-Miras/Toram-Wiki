from bson import CodecOptions
from bson.codec_options import TypeRegistry
from pydantic import BaseModel as PydanticBaseModel
from pymongo import MongoClient

from database.codec import CollectionCodec, DiscordEmbedCodec
from database.types import mongo_database, mongo_collection


class WhiskeyDatabase:

    def __init__(self, client: MongoClient):
        # discord database
        self.discord: mongo_database = client.discord

        # items database
        self.items: mongo_database = client.items

        # monsters database
        self.monsters: mongo_database = client.monsters

        # mementos database
        self.mementos: mongo_database = client.mementos

        self.pages: mongo_database = client.pages

    @property
    def discord_guilds(self) -> mongo_collection:
        return self.discord.guilds

    @property
    def discord_users(self) -> mongo_collection:
        return self.discord.users

    @property
    def items_leaf(self) -> mongo_collection:
        return self.items.items.leaf

    @property
    def items_composite(self) -> mongo_collection:
        return self.items.items.composite

    @property
    def monsters_composite(self) -> mongo_collection:
        return self.monsters.monsters.composite

    @property
    def monsters_leaf(self) -> mongo_collection:
        return self.monsters.monsters.leaf

    @property
    def pages_help(self) -> mongo_collection:
        return self.pages.get_collection(
            'pages.help', codec_options=CodecOptions(type_registry=TypeRegistry([DiscordEmbedCodec()]))
        )

    @property
    def items_leaf_mementos(self) -> mongo_collection:
        return self.mementos.get_collection(
            'items.items.leaf', codec_options=CodecOptions(type_registry=TypeRegistry([CollectionCodec()]))
        )


class QueryInformation(PydanticBaseModel):
    collection: mongo_collection
    to_search: str

    class Config:
        arbitrary_types_allowed = True
