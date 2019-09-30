import argparse
import asyncio
import json

import aiohttp

from mirror_clients.elasticsearch_client import ElasticSearchClient
from mirror_clients.mongodb_client import MongoClient

CLIENTS = {
    'mongodb': MongoClient,
    'elasticsearch': ElasticSearchClient
}


class MongoMirrorOperation:
    UPSERT = 'upsert'
    UPDATE = 'update'
    DELETE = 'delete'
    NOOP = 'noop'


class MongoMirrorRequest:
    PROTOCOL = 'protocol-request'
    TIMESTAMP = 'timestamp-request'
    INIT_POINT = 'init-point-request'
    IDS_SINCE_TIMESTAMP = 'ids-since-timestamp-request'


async def sync(mirror_url, client_url, client_name, protocol):
    client = CLIENTS[client_name](client_url, protocol)
    session = aiohttp.ClientSession()

    operation_mapping = {
        MongoMirrorRequest.PROTOCOL: client.get_protocol,
        MongoMirrorRequest.INIT_POINT: client.get_initial_point,
        MongoMirrorRequest.TIMESTAMP: client.get_timestamp,
        MongoMirrorRequest.IDS_SINCE_TIMESTAMP: client.get_ids_since_timestamp,
        MongoMirrorOperation.UPSERT: client.upsert,
        MongoMirrorOperation.UPDATE: client.update,
        MongoMirrorOperation.DELETE: client.delete,
        MongoMirrorOperation.NOOP: client.noop,
    }

    async with session.ws_connect(mirror_url) as ws:
        async for msg in ws:
            print(f'Received {msg.data}')
            received_data = json.loads(msg.data)
            data = received_data.copy()
            op_type = data.pop('type')
            await client.serialize_fields(data)

            result = await operation_mapping[op_type](**data)
            if result is not None:
                received_data['data'] = result
                await ws.send_json(received_data)


def _handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mirror_url', '-m', help="Mirror server url", type=str, required=True)
    parser.add_argument('--client_url', '-u', help="Client db url", type=str, required=True)
    parser.add_argument('--client_name', '-n', help="Client name [mongodb/elasticsearch]", type=str, required=True)
    parser.add_argument('--protocol', '-p', help="Protocol [full/simple]", type=str, required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = _handle_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sync(**vars(args)))
