from abc import abstractmethod, ABC

from pymongo.command_cursor import CommandCursor

from database import indexes
from database.models import QueryInformation


class SearchStrategy(ABC):

    @abstractmethod
    def query(self, query: QueryInformation) -> CommandCursor:
        pass


class EdgeGramSearch(SearchStrategy):

    def query(self, query: QueryInformation) -> CommandCursor:
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
                '$limit': 100
            }
        ])


class TriGramSearch(SearchStrategy):

    def query(self, query: QueryInformation) -> CommandCursor:
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
                '$limit': 100
            }
        ])


class TitleSearch(SearchStrategy):

    def query(self, query: QueryInformation) -> list[dict]:
        ...
