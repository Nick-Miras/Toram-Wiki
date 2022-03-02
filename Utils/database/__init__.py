import os

import pymongo
from pymongo import MongoClient

global_dict = {}


class Client:
    CLUSTER = MongoClient(os.environ['MONGOCLIENT'])
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
