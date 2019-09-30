import argparse

from mirror_clients.elasticsearch_client import INDEX, TS_INDEX, db
from elasticsearch import Elasticsearch


def create_index(_db):
    _db.indices.create(index=INDEX, ignore=400, body={
        'mappings': {
            'properties': {
                '_last_modified': {'type': 'date'},
                'timer': {'type': 'date'},
                'spec._fields.allowedValues': {'type': 'text'}
            }
        }
    })

    _db.indices.create(index=TS_INDEX, ignore=400, body={
        'mappings': {
            'properties': {
                'time': {'type': 'long'},
            }
        }
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client_url', '-u', help="Client db url", type=str, required=True)
    args = parser.parse_args()
    db = Elasticsearch(hosts=[args.client_url])
    create_index(db)
    print('Done')
