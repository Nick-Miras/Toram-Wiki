import os

import pymongo
from pymongo import MongoClient

global_dict = {}


class DatabaseException(Exception):
    pass


class ItemNotFound(DatabaseException):
    def __init__(self, item=None):
        super().__init__(f'{item or "Item"} cannot be found.')


class Client:
    CLUSTER = MongoClient(  # Temporary
        os.environ['MONGOCLIENT']
    )  # TODO: Remove Temporary Database Key

    DISCORD = CLUSTER['discord']
    WIKI = CLUSTER['wiki']


class Database:
    USERS = Client.DISCORD['users']
    GUILDS = Client.DISCORD['guilds']
    CATEGORIES = Client.WIKI['categories']
    ITEMS = Client.WIKI['items new']  # TODO: Remove Old Database

    @classmethod
    def exists(cls, collection: pymongo.collection.Collection, lookup: dict) -> bool:
        return bool(collection.count_documents(lookup))
