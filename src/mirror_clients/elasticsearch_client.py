import logging
from datetime import datetime

from elasticsearch_async import AsyncElasticsearch

from mirror_clients.base import FullMirrorClient

LOG = logging.getLogger('elasticsearch_client')

ISO_DATETIME = '%Y-%m-%dT%H:%M:%S.%f'


class ElasticSearchClient(FullMirrorClient):

    def __init__(self, client_url, client_namespace):
        self.db = self.__init_db(client_url)
        self.index = client_namespace
        self.index_ts = f'{client_namespace}_ts'
        
    def __init_db(self, client_url):
        return AsyncElasticsearch(hosts=[client_url])

    async def _save_timestamp(self, _id, ts):
        if not ts:
            ts = {}
        await self.db.index(index=self.index_ts, id=_id, body=ts)

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

    async def get_timestamp(self, **kwargs):
        response = await self.db.search(
            index=self.index_ts,
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
