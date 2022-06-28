from enum import Enum


class AggregationIndexes(Enum):
    ItemsCompositeEdgeGram = 'items.composite edgegram'
    ItemsCompositeTriGram = 'items.composite trigram'
    MonstersCompositeEdgeGram = 'monsters.composite edgegram'
    MonstersCompositeTriGram = 'monsters.composite trigram'
