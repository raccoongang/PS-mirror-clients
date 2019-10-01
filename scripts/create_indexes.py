import argparse

from elasticsearch import Elasticsearch


def create_index(_db, index):
    _db.indices.create(index=index, ignore=400, body={
        'mappings': {
            'properties': {
                '_last_modified': {'type': 'date'},
                'timer': {'type': 'date'},
                'spec._fields.allowedValues': {'type': 'text'}
            }
        }
    })

    _db.indices.create(index=f'{index}_ts', ignore=400, body={
        'mappings': {
            'properties': {
                'time': {'type': 'long'},
            }
        }
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client_url', '-u', help="Client db url", type=str, required=True)
    parser.add_argument('--index', '-i', help="Client index", type=str, required=True)
    args = parser.parse_args()

    db = Elasticsearch(hosts=[args.client_url])
    create_index(db, args.index)
    print('Done')
