from enum import Enum


class AggregationIndexes(Enum):
    ItemsCompositeEdgeGram = 'items.composite edgegram'
    ItemsCompositeTriGram = 'items.composite trigram'
    ItemsCompositeString = 'items.composite string'
    MonstersCompositeEdgeGram = 'monsters.composite edgegram'
    MonstersCompositeTriGram = 'monsters.composite trigram'
    MonstersCompositeString = 'monsters.composite string'
