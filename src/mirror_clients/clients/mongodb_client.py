import asyncio
import logging

from bson import timestamp, ObjectId
from motor import motor_asyncio

from mirror_clients import utils
from mirror_clients.base import FullMirrorClient

LOG = logging.getLogger('mongodb_client')


class MongoClient(FullMirrorClient):
    client_name = 'mongodb'

    def __init__(self, client_url, client_namespace):
        client_db, collection = utils.namespace_to_db_collection(client_namespace)
        collection_ts = f'{collection}_ts'
        self.db = self.__init_db(client_url, client_db, collection_ts)
        self.collection = self.db[collection]
        self.collection_ts = self.db[collection_ts]

    def __init_db(self, client_url, client_db, collection_ts_name):
        mongo = motor_asyncio.AsyncIOMotorClient(client_url)
        db = mongo[client_db]
        asyncio.create_task(self.__create_index(db[collection_ts_name]))
        return db

    async def __create_index(self, collection_ts):
        await collection_ts.create_index('ts', sparse=True, background=True)

    async def _save_timestamp(self, _id, ts):
        await self.collection_ts.replace_one({'_id': _id}, {'_id': _id, 'ts': ts}, upsert=True)

    async def get_initial_point(self, **kwargs):
        doc = await self.collection.find_one({}, {'_last_modified': 1, '_id': 0}, sort=[('_last_modified', -1)])
        return doc['_last_modified'] if doc else ''

    async def upsert(self, data, ts):
        await self.collection.replace_one({'_id': data['_id']}, data, upsert=True)
        await self._save_timestamp(data['_id'], ts)

    async def delete(self, data, ts):
        await self.collection.delete_one(data)
        await self._save_timestamp(data['_id'], ts)

    async def update(self, data, ts):
        _id = data.pop('_id')
        await self.collection.update_one({'_id': _id}, {'$set': data['$set']})
        await self._save_timestamp(_id, ts)

    async def noop(self, data, ts):
        LOG.info(f'data - {data}, ts - {ts}')

    async def get_timestamp(self, **kwargs):
        doc = await self.collection_ts.find_one({}, {'ts': 1, '_id': 0}, sort=[('ts', -1)])
        return [doc['ts'].time, doc['ts'].inc] if doc and doc['ts'] else ''

    async def get_ids_since_timestamp(self, data, ts):
        return [str(doc['_id']) async for doc in self.collection_ts.find({'ts': {'$gt': ts}}, {'ts': 0})]

    @staticmethod
    async def serialize_fields(response_data):
        if '_id' in response_data['data']:
            response_data['data']['_id'] = ObjectId(response_data['data']['_id'])
        ts = response_data.get('ts')
        if ts:
            response_data['ts'] = timestamp.Timestamp(*ts)
