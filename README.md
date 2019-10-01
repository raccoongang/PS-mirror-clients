# mirror-clients
## Overview
Client for synchronization data through Prozorro-sale Mirror

#### Implemented full protocol clients:

- MongoClient
- ElasticSearchClient

## Getting Started
mirror-clients supports Python 3.6+

### For implemented clients
#### Build
```
docker build -t mirror-clients .
```
#### Run
To run mirror-client use command:
```
docker run mirror-clients -m mirror_url -u client_url -n client_name -ns client_namespace
```
- -m - mirror url
- -u - client url
- -n - client name, set as client class attribute (`mongodb`, `elasticsearch`, etc.)
- -ns - client namespace (for mongodb `db.collection`, for elasticsearch `index`)

#### Examples:
#### To run mirror-clients for mongodb:
```
docker run mirror-clients -m http://0.0.0.0:8080/ws -u mongodb://localhost:27017 -n mongodb -ns procedures.procedures
```

#### To run mirror-clients for elasticsearch:

If indexes is not created, firstly run:
```
python3 scripts/create_indexes.py -u localhost -i procedures
```
- -u - client url
- -i - index

```
docker run mirror-clients -m http://0.0.0.0:8187/ws -u localhost -n elasticsearch -ns procedures
```

### For custom clients
#### mirror-clients maintain 2 client protocol

SimpleMirrorClient protocol have to implement next operations:

- upsert
- noop
- get_initial_point
- get_timestamp

FullMirrorClient protocol have to implement next operation:

- upsert
- noop
- get_initial_point
- get_timestamp
- update
- delete
- get_ids_since_timestamp

To create custom client you should create your file inside `mirror_clients/clients` dir,
create custom class and inherit it from one of the described above,
implement abstract method and set `client_name` as class attribute.
Go to the `mirror_clients/sync_session.py` file and import your custom class.

Then build and run as described in the `For implemented clients` section.



# If you are not familiar with `docker`

### Installation
```
pip install mirror-clients
```
### Running
```
python3 mirror_clients/sync_session.py -m mirror_url -u client_url -n client_name -ns client_namespace
```
