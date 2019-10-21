import argparse
import asyncio
import json
import os
import logging
from datetime import datetime

import aiohttp

from mirror_clients.base import SimpleMirrorClient, FullMirrorClient
from mirror_clients.clients.elasticsearch_client import ElasticSearchClient
from mirror_clients.clients.mongodb_client import MongoClient
from aiohttp.client_exceptions import WSServerHandshakeError

CLIENTS = {}
CLIENT_AUTH_TOKEN = os.environ['AUTH_TOKEN']
LOG = logging.getLogger('sync_session')


def _update_client_mapping():
    global CLIENTS
    client_list = SimpleMirrorClient.__subclasses__() + FullMirrorClient.__subclasses__()
    for sub_cls in client_list:
        CLIENTS[sub_cls.client_name] = sub_cls


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


async def sync(mirror_url, client):
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

    async with session.ws_connect(mirror_url, headers={'Authorization': CLIENT_AUTH_TOKEN}) as ws:
        start_time = datetime.now()
        count = 0

        async for msg in ws:
            count += 1
            received_data = json.loads(msg.data)
            data = received_data.copy()
            op_type = data.pop('type')
            await client.serialize_fields(data)

            result = await operation_mapping[op_type](**data)
            if (datetime.now() - start_time).seconds >= 1:
                LOG.info(f'Object per second - {count}')
                count = 0
                start_time = datetime.now()

            if result is not None:
                received_data['data'] = result
                await ws.send_json(received_data)


async def sync_session(args):
    sync_client = CLIENTS[args.client_name](args.client_url, args.client_namespace)
    try:
        await sync(mirror_url=args.mirror_url, client=sync_client)
    except WSServerHandshakeError as error:
        if error.status == 403:
            LOG.warning('Not authorized')
        else:
            LOG.exception(error.message)


def _handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mirror_url', '-m', help="Mirror server url", type=str, required=True)
    parser.add_argument('--client_url', '-u', help="Client db url", type=str, required=True)
    parser.add_argument('--client_name', '-n', help="Client name [mongodb||elasticsearch]", type=str, required=True)
    parser.add_argument('--client_namespace', '-ns', help="Client namespace [db.collection||index]", type=str, required=True)
    return parser.parse_args()


if __name__ == '__main__':
    log_level = os.getenv('LOGGING_LEVEL', 'INFO')
    logging.basicConfig(level=log_level)
    LOG.info("Starting client")
    _update_client_mapping()
    arguments = _handle_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sync_session(arguments))

