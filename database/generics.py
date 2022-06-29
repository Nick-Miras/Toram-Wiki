from bson import ObjectId

from database import mongo_collection


def mongodb_cascade_delete(collection: mongo_collection, foreign_key: str, to_delete: ObjectId) -> None:
    """
    mongodb cascade delete using a foreign key
    """
    results = collection.aggregate(
        [
            {
                '$match': {
                    '_id': to_delete
                }
            },
            {
                '$graphLookup': {
                    'from': 'database',
                    'startWith': to_delete,
                    'connectFromField': '_id',
                    'connectToField': foreign_key,
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
    mongo_collection.delete_many({'_id': {'$in': [document['_id'] for document in results]}})
