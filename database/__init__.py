from hydra import compose, initialize
from omegaconf import DictConfig
from pymongo import MongoClient

from database.codec import CollectionCodec
from database.exceptions import DatabaseNotFound, CollectionNotFound
from database.types import mongo_collection, mongo_database

global_dict = {}


def get_mongodb_client() -> MongoClient:
    with initialize(config_path='../config/database/'):
        cfg: DictConfig = compose(config_name='mongodb')
        return MongoClient(cfg.connection_string)
