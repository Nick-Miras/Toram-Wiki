from abc import ABC, abstractmethod
from typing import Type, Optional, Generator, TypeVar, Generic, TypeAlias

from bson import ObjectId
from pydantic import BaseModel as PydanticBaseModel, Extra
from pydantic.generics import GenericModel as PydanticGenericModel
from pymongo import (
    InsertOne as MongoInsertOne,
    DeleteOne as MongoDeleteOne,
    DeleteMany as MongoDeleteMany,
    UpdateOne as MongoUpdateOne,
    UpdateMany as MongoUpdateMany
)

from database import mongo_collection
from database.exceptions import CommandNotFound

DataD = TypeVar('DataD')
PymongoOperationType: TypeAlias = MongoInsertOne | MongoDeleteOne | MongoDeleteMany | MongoUpdateOne | MongoUpdateMany


class DatabaseCommand(PydanticGenericModel, Generic[DataD], ABC):
    name: str
    collection: mongo_collection
    data: DataD

    def __init__(self, *, collection: mongo_collection, data: DataD, **_):
        super().__init__(name=self.__class__.__name__, collection=collection, data=data)

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def execute(self):
        pass

    @classmethod
    def get_subclass(cls, command: str) -> Type['DatabaseCommand']:
        for command_cls in cls.__subclasses__():
            if command == command_cls.__name__:
                return command_cls
        raise CommandNotFound()


class InsertOne(DatabaseCommand[dict]):

    def execute(self):
        self.collection.insert_one(self.data)


class InsertMany(DatabaseCommand[list[dict]]):

    def execute(self):
        self.collection.insert_many(self.data)


class BulkWrite(DatabaseCommand[list[PymongoOperationType]]):

    def execute(self):
        self.collection.bulk_write(self.data)


class CommandMemento(PydanticBaseModel):
    next: Optional[ObjectId] = None
    command: DatabaseCommand
    current: bool

    class Config:
        extra = Extra.ignore
        arbitrary_types_allowed = True


class DatabaseOperations:  # controller

    def __init__(self, collection: mongo_collection):
        """The Command Controller as dictated by the Command Design Pattern

        Args:
            collection (mongo_collection): The Collection to use to store the mementos
        """
        self.mementos = collection

    @property
    def current(self) -> Optional[ObjectId]:
        try:
            return next(self.mementos.find({'current': True}, {'_id': 1}).sort('_id', -1).limit(1))['_id']
        except StopIteration:
            return

    def get_next_of(self, document_id: ObjectId) -> Optional[ObjectId]:
        if next_document := self.mementos.find_one({'_id': document_id}, {'next': 1}):
            return next_document['next']

    def get_parent_of(self, document_id: ObjectId) -> Optional[ObjectId]:
        if parent_document := self.mementos.find_one({'next': document_id}, {'_id': 1}):
            return parent_document['_id']

    def register(self, command: DatabaseCommand):
        self._append_memento(CommandMemento(command=command, current=True))

    def _fetch_mementos(self) -> Generator[CommandMemento, None, None]:
        every_memento = self.mementos.find({})
        for memento in every_memento:
            command = memento.pop('command')
            command_cls = DatabaseCommand.get_subclass(command['name']).parse_obj(command)
            yield CommandMemento(command=command_cls, **memento)

    def _delete_mementos_from(self, object_id: ObjectId):
        # recursively delete mementos starting from :param object_id: document
        results = self.mementos.aggregate(
            [
                {
                    '$match': {
                        '_id': object_id
                    }
                },
                {
                    '$graphLookup': {
                        'from': 'database',
                        'startWith': object_id,
                        'connectFromField': 'next',
                        'connectToField': '_id',
                        'as': 'toDelete'
                    }
                },
                {
                    '$unwind': '$toDelete'
                },
                {
                    '$project': {
                        '_id': '$toDelete._id'
                    }
                }
            ]
        )
        if len(document_ids := [document['_id'] for document in results]) != 0:
            self.mementos.bulk_write([MongoDeleteOne({'_id': _}) for _ in document_ids])

    def _append_memento(self, memento: CommandMemento):
        old_current = self.current
        self.mementos.insert_one(memento.dict(by_alias=True))
        if old_current:
            self.mementos.update_one({'_id': old_current}, {'$set': {'next': self.current, 'current': False}})
            if object_id := self.get_next_of(old_current):
                self._delete_mementos_from(object_id)

    def undo(self):
        current = self.current
        if document_id_of_parent := self.get_parent_of(current):
            self.mementos.bulk_write([
                MongoUpdateOne({'_id': current}, {'$set': {'current': False}}),
                MongoUpdateOne({'_id': document_id_of_parent}, {'$set': {'current': True}})
            ])

    def redo(self):
        current = self.current
        if document_id_of_next := self.get_next_of(current):
            self.mementos.bulk_write([
                MongoUpdateOne({'_id': current}, {'$set': {'current': False}}),
                MongoUpdateOne({'_id': document_id_of_next}, {'$set': {'current': True}})
            ])

    def clear_mementos(self):
        self.mementos.delete_many({})

    def execute_commands(self):
        for memento in self._fetch_mementos():
            memento.command.execute()
