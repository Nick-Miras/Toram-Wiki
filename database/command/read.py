from abc import abstractmethod, ABC

from pymongo.command_cursor import CommandCursor

from database.indexes import AggregationIndexes
from database.models import QueryInformation


class SearchStrategy(ABC):

    @abstractmethod
    def query(self, query: QueryInformation, index: AggregationIndexes, *, limit: int = 100) -> CommandCursor:
        pass


class AutoCompleteSearch(SearchStrategy):

    def query(self, query: QueryInformation, index: AggregationIndexes, *, limit: int = 100) -> CommandCursor:
        return query.collection.aggregate([
            {
                '$search': {
                    'index': index.value,
                    'autocomplete': {
                        'query': query.to_search,
                        'path': 'name',
                        'fuzzy': {
                            'maxEdits': 2,
                            'prefixLength': 1
                        }
                    },
                    'highlight': {
                        'path': 'name',
                    }
                }
            }, {
                '$addFields': {
                    'highlights': {
                        '$meta': 'searchHighlights'
                    }
                }
            }, {
                '$sort': {
                    'highlights.score': -1
                }
            }, {
                '$limit': limit
            }
        ])


class TitleSearch(SearchStrategy):

    def query(self, query: QueryInformation, index: AggregationIndexes, *, limit: int = 100) -> CommandCursor:
        ...
