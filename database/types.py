from typing import TypeAlias

import pymongo.database

mongo_collection: TypeAlias = pymongo.collection.Collection
mongo_database: TypeAlias = pymongo.database.Database
