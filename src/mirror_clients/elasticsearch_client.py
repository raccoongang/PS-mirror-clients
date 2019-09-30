import logging
from datetime import datetime

from elasticsearch_async import AsyncElasticsearch

LOG = logging.getLogger('elasticsearch_client')

ISO_DATETIME = '%Y-%m-%dT%H:%M:%S.%f'

_db = None


def db(client_url):
    global _db
    if _db is None:
        _db = AsyncElasticsearch(hosts=[client_url])
    return _db


class ElasticSearchClient:
    def __init__(self, client_url, client_namespace, protocol):
        self.db = db(client_url)
        self._protocol = protocol
        self.index = client_namespace
        self.ts_index = f'{client_namespace}_ts'

    async def _save_timestamp(self, _id, ts):
        if not ts:
            ts = {}
        await self.db.index(index=self.ts_index, id=_id, body=ts)

    async def get_initial_point(self, **kwargs):
        response = await self.db.search(
            index=self.index,
            filter_path=['hits.hits._source._last_modified'],
            body={
                "size": 1,
                "sort": {
                    "_last_modified": {
                        "order": "desc"
                    }
                }
            })

        return response['hits']['hits'][0]['_source']['_last_modified'] if response else ''

    async def upsert(self, data, ts):
        _id = data.pop('_id')
        await self.db.index(index=self.index, id=_id, body=data)
        await self._save_timestamp(_id, ts)

    async def delete(self, data, ts):
        await self.db.delete(index=self.index, id=data['_id'])
        await self._save_timestamp(data['_id'], ts)

    async def update(self, data, ts):
        _id = data.pop('_id')
        await self.db.index(index=self.index, id=_id, body=data['$set'])
        await self._save_timestamp(_id, ts)

    async def noop(self, data, ts):
        LOG.info(f'data - {data}, ts - {ts}')

    async def get_protocol(self, **kwargs):
        return self._protocol

    async def get_timestamp(self, **kwargs):
        response = await self.db.search(
            index=self.ts_index,
            filter_path=['hits.hits._source'],
            body={
                "size": 1,
                "sort": {
                    "time": {
                        "order": "desc"
                    }
                }
            })

        ts = response['hits']['hits'][0]['_source'] if response else None
        return [ts['time'], ts['inc']] if ts else ''

    async def get_ids_since_timestamp(self, data, ts):
        pass

    @staticmethod
    async def serialize_fields(response_data):
        ts = response_data.get('ts')
        if ts:
            response_data['ts'] = {'time': ts[0], 'inc': ts[1]}
        if '_last_modified' in response_data['data']:
            last_modified = response_data['data']['_last_modified']
            response_data['data']['_last_modified'] = datetime.strptime(last_modified, ISO_DATETIME)
