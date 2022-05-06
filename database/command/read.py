from abc import abstractmethod, ABC

from pymongo.command_cursor import CommandCursor

from database import indexes
from database.models import QueryInformation


class SearchStrategy(ABC):

    @abstractmethod
    def query(self, query: QueryInformation, limit: int = 100) -> CommandCursor:
        pass


class EdgeGramSearch(SearchStrategy):

    def query(self, query: QueryInformation, *, limit: int = 100) -> CommandCursor:
        return query.collection.aggregate([
            {
                '$search': {
                    'index': indexes.ItemsCompositeEdgeGram,
                    'autocomplete': {
                        'query': query.to_search,
                        'path': 'name',
                        'fuzzy': {
                            'maxEdits': 1,
                            'prefixLength': 1
                        }
                    }
                }
            }, {
                '$addFields': {
                    'score': {
                        '$meta': 'searchScore'
                    }
                }
            }, {
                '$sort': {
                    'score': -1
                }
            }, {
                '$limit': limit
            }
        ])


class TriGramSearch(SearchStrategy):

    def query(self, query: QueryInformation, limit: int = 100) -> CommandCursor:
        return query.collection.aggregate([
            {
                '$search': {
                    'index': indexes.ItemsCompositeTriGram,
                    'autocomplete': {
                        'query': query.to_search,
                        'path': 'name',
                        'fuzzy': {
                            'maxEdits': 1,
                            'prefixLength': 0
                        }
                    }
                }
            }, {
                '$addFields': {
                    'score': {
                        '$meta': 'searchScore'
                    }
                }
            }, {
                '$sort': {
                    'score': -1
                }
            }, {
                '$limit': limit
            }
        ])


class TitleSearch(SearchStrategy):

    def query(self, query: QueryInformation, limit: int = 100) -> list[dict]:
        ...
