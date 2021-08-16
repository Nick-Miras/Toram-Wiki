import os
import discord
import pymongo
from pymongo import MongoClient
import ssl
import inspect
import pickle

global_dict = {}


class DatabaseException(Exception):
    pass


class ItemNotFound(DatabaseException):
    def __init__(self, item=None):
        item = item if item else 'Item'
        super().__init__(f'{item} cannot be found.')


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
    ITEMS = Client.WIKI['items']

    @classmethod
    def exists(cls, collection: pymongo.collection.Collection, lookup: dict) -> bool:
        return bool(collection.count_documents(lookup))
