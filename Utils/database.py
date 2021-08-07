import os
import discord
import pymongo
from pymongo import MongoClient
import ssl


__all__ = (
    'Database'
)


class DatabaseException(Exception):
    pass


class ItemNotFound(DatabaseException):
    def __init__(self, item=None):
        item = item if item else 'Item'
        super().__init__(f'{item} cannot be found.')


class Client:
    CLUSTER = MongoClient(
        os.environ['MONGODB'],
        ssl=True,
        ssl_cert_reqs=ssl.CERT_NONE
    )

    DISCORD = CLUSTER['discord']
    WIKI = CLUSTER['wiki']


class Database:
    USERS = Client.DISCORD['users']
    GUILDS = Client.DISCORD['guilds']
    CATEGORIES = Client.WIKI['categories']
    ITEMS = Client.WIKI['items']

    @classmethod
    def exists(cls, collection: pymongo.collection.Collection, lookup: dict) -> bool:
        if collection.find_one(lookup):
            return True
        return False
