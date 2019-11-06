import argparse
import asyncio
import json
import os
import logging
import signal
from enum import Enum
from datetime import datetime
import uvloop

import aiohttp

from mirror_clients.base import SimpleMirrorClient, FullMirrorClient
from mirror_clients.clients import *
from aiohttp.client_exceptions import WSServerHandshakeError

CLIENTS = {}
CLIENT_AUTH_TOKEN = os.environ['AUTH_TOKEN']
LOG = logging.getLogger('sync_session')


def _update_client_mapping():
    global CLIENTS
    client_list = SimpleMirrorClient.__subclasses__() + FullMirrorClient.__subclasses__()
    for sub_cls in client_list:
        CLIENTS[sub_cls.client_name] = sub_cls


class MongoMirrorOperation(Enum):
    UPSERT = 'upsert'
    UPDATE = 'update'
    DELETE = 'delete'
    NOOP = 'noop'


class MongoMirrorRequest(Enum):
    PROTOCOL = 'protocol-request'
    TIMESTAMP = 'timestamp-request'
    INIT_POINT = 'init-point-request'
    IDS_SINCE_TIMESTAMP = 'ids-since-timestamp-request'


async def sync(mirror_url, client):
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

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(mirror_url, headers={'Authorization': CLIENT_AUTH_TOKEN}) as ws:
            start_time = datetime.now()
            count = 0
            while True:
                data = await ws.receive_json()
                count += 1
                # save original data to resend it back in response
                request = data.copy()

                op_type = data.pop('type')
                try:
                    op_type = MongoMirrorOperation(op_type)
                except ValueError:
                    op_type = MongoMirrorRequest(op_type)

                result = await operation_mapping[op_type](**data)
                if op_type in MongoMirrorRequest:
                    request['data'] = result
                    await ws.send_json(request)

                if (datetime.now() - start_time).seconds >= 1:
                    LOG.info(f'Object per second - {count}')
                    count = 0
                    start_time = datetime.now()


async def sync_session(args):
    sync_client = CLIENTS[args.client_name](args.client_url, args.client_namespace)
    task = asyncio.create_task(sync(mirror_url=args.mirror_url, client=sync_client))

    def stop_callback(signum, frame):
        LOG.info('Received shutdown signal. Stopping client...')
        task.cancel()

    signal.signal(signal.SIGTERM, stop_callback)
    signal.signal(signal.SIGINT, stop_callback)

    try:
        r = await task
        r.result()
    except WSServerHandshakeError as error:
        if error.status == 403:
            LOG.warning('Not authorized')
        else:
            LOG.exception(error.message)
    except asyncio.CancelledError:
        LOG.exception('Caught error')
        return


def _handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mirror_url', '-m', help="Mirror server url", type=str, required=True)
    parser.add_argument('--client_url', '-u', help="Client db url", type=str, required=True)
    parser.add_argument('--client_name', '-n', help=f"Client name [{'|'.join(CLIENTS.keys())}]", type=str, required=True)
    parser.add_argument('--client_namespace', '-ns', help="Client namespace [db.collection||index]", type=str, required=True)
    return parser.parse_args()


if __name__ == '__main__':
    log_level = os.getenv('LOGGING_LEVEL', 'INFO')
    logging.basicConfig(level=log_level)
    LOG.info("Starting client")
    _update_client_mapping()
    arguments = _handle_args()
    uvloop.install()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sync_session(arguments))
