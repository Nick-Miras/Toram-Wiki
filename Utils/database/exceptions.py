class DatabaseException(Exception):
    ...


class ItemNotFound(DatabaseException):
    def __init__(self, item=None):
        super().__init__(f'{item or "Item"} cannot be found.')
