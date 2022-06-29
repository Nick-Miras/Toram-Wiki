import discord
from bson.codec_options import TypeCodec

import database
from database.exceptions import DatabaseNotFound, CollectionNotFound
from database.types import mongo_collection


def split_collection_full_name(collection: str) -> tuple[str, str]:
    """
    Args:
        collection: The pymongo collection represented as a string

    Returns:
        A tuple of strings where the first string is the name of the database
        and the second string is the collection in the database or None
    """
    if len(collection_full_name := collection.split('.', maxsplit=1)) == 2:
        db, collection = collection_full_name
        return db, collection
    raise ValueError(f'{collection} is not a valid collection string')


def is_collection_string(string: str) -> bool:
    try:
        split_collection_full_name(string)
    except ValueError:
        return False
    return True


def collection_string_to_obj(collection_string: str) -> mongo_collection:
    mongo_client = database.get_mongodb_client()
    db, collection = split_collection_full_name(collection_string)
    if db not in mongo_client.list_database_names():
        raise DatabaseNotFound(db)
    if collection not in mongo_client[db].list_collection_names():
        raise CollectionNotFound(collection)
    return database.get_mongodb_client()[db][collection]


class CollectionCodec(TypeCodec):
    python_type = mongo_collection
    bson_type = str

    def transform_python(self, value: mongo_collection) -> str:
        """Function that transforms a custom type value into a type
        that BSON can encode."""
        return value.full_name

    def transform_bson(self, value: str) -> str | mongo_collection:
        """Function that transforms a vanilla BSON type value into our
        custom type."""
        try:
            return collection_string_to_obj(value)
        except (DatabaseNotFound, CollectionNotFound, ValueError):
            return value


class DiscordEmbedCodec(TypeCodec):
    python_type = discord.Embed
    bson_type = dict

    def transform_python(self, value: discord.Embed) -> dict:
        """Function that transforms a custom type value into a type
        that BSON can encode."""
        return value.to_dict()

    def transform_bson(self, value: dict) -> dict | discord.Embed:
        """Function that transforms a vanilla BSON type value into our
        custom type."""
        try:
            return discord.Embed.from_dict(value)
        except (DatabaseNotFound, CollectionNotFound, ValueError):
            return value
