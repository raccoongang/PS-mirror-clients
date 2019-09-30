import asyncio
import logging

from bson import timestamp, ObjectId
from motor import motor_asyncio

LOG = logging.getLogger('mongodb_client')

_db = None


async def _create_index(_db):
    await _db.procedures_ts.create_index('ts', sparse=True)


def db(client_url):
    global _db
    if _db is None:
        mongo = motor_asyncio.AsyncIOMotorClient(client_url, w='majority')
        _db = mongo.procedures1
        asyncio.create_task(_create_index(_db))
    return _db


class MongoClient:
    def __init__(self, client_url, protocol):
        self.db = db(client_url)
        self._protocol = protocol

    async def _save_timestamp(self, _id, ts):
        await self.db.procedures_ts.replace_one({'_id': _id}, {'_id': _id, 'ts': ts}, upsert=True)

    async def get_initial_point(self, **kwargs):
        doc = await self.db.procedures.find_one({}, {'_last_modified': 1, '_id': 0}, sort=[('_last_modified', -1)])
        return doc['_last_modified'] if doc else ''

    async def upsert(self, data, ts):
        await self.db.procedures.replace_one({'_id': data['_id']}, data, upsert=True)
        await self._save_timestamp(data['_id'], ts)

    async def delete(self, data, ts):
        await self.db.procedures.delete_one(data)
        await self._save_timestamp(data['_id'], ts)

    async def update(self, data, ts):
        _id = data.pop('_id')
        await self.db.procedures.update_one({'_id': _id}, {'$set': data['$set']})
        await self._save_timestamp(_id, ts)

    async def noop(self, data, ts):
        LOG.info(f'data - {data}, ts - {ts}')

    async def get_protocol(self, **kwargs):
        return self._protocol

    async def get_timestamp(self, **kwargs):
        doc = await self.db.procedures_ts.find_one({}, {'ts': 1, '_id': 0}, sort=[('ts', -1)])
        return [doc['ts'].time, doc['ts'].inc] if doc and doc['ts'] else ''

    async def get_ids_since_timestamp(self, data, ts):
        return [str(doc['_id']) async for doc in self.db.procedures_ts.find({'ts': {'$gt': ts}}, {'ts': 0})]

    @staticmethod
    async def serialize_fields(response_data):
        if '_id' in response_data['data']:
            response_data['data']['_id'] = ObjectId(response_data['data']['_id'])
        ts = response_data.get('ts')
        if ts:
            response_data['ts'] = timestamp.Timestamp(*ts)
