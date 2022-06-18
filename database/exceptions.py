class MongoException(Exception):
    pass


class ItemNotFound(MongoException):
    def __init__(self, item=None):
        super().__init__(f'{item or "Item"} cannot be found.')


class DatabaseNotFound(MongoException):
    def __init__(self, database):
        super().__init__(f'`{database}` is not a valid database.')


class CollectionNotFound(MongoException):
    def __init__(self, collection):
        super().__init__(f'`{collection}` is not a valid collection.')


class CommandNotFound(Exception):
    def __init__(self):
        super().__init__('Command Not Found')
