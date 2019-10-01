class Protocol:
    SIMPLE = 'simple'
    FULL = 'full'


class SimpleMirrorClient:
    """
    Abstract Class for the simple client realization
    """
    _protocol = Protocol.SIMPLE
    client_name = None

    async def get_protocol(self, **kwargs):
        """
        Method to return _protocol.
        Handle the `protocol-request` operation from the mirror
        """
        return self._protocol

    async def _save_timestamp(self, _id, ts):
        """
        Method to save timestamp
        """
        raise NotImplementedError

    async def get_initial_point(self, **kwargs):
        """
        Method to get _last_modified value from the last object.
        Handle the `init-point-request` operation from the mirror
        """
        raise NotImplementedError

    async def upsert(self, data, ts):
        """
        Method to upsert data.
        Handle the `upsert` operation from the mirror
        """
        raise NotImplementedError

    async def noop(self, data, ts):
        """
        Handle the `noop` operation from the mirror
        """
        raise NotImplementedError

    async def get_timestamp(self, **kwargs):
        """
        Method to get latest timestamp.
        Handle the `timestamp-request` operation from the mirror
        """
        raise NotImplementedError


class FullMirrorClient:
    """
    Abstract Class for the full client realization
    """
    _protocol = Protocol.FULL
    client_name = None

    async def get_protocol(self, **kwargs):
        """
        Method to return _protocol.
        Handle the `protocol-request` operation from the mirror
        """
        return self._protocol

    async def _save_timestamp(self, _id, ts):
        """
        Method to save timestamp
        """
        raise NotImplementedError

    async def get_initial_point(self, **kwargs):
        """
        Method to get _last_modified value from the last object.
        Handle the `init-point-request` operation from the mirror
        """
        raise NotImplementedError

    async def upsert(self, data, ts):
        """
        Method to upsert data.
        Handle the `upsert` operation from the mirror
        """
        raise NotImplementedError

    async def noop(self, data, ts):
        """
        Handle the `noop` operation from the mirror
        """
        raise NotImplementedError

    async def get_timestamp(self, **kwargs):
        """
        Method to get latest timestamp.
        Handle the `timestamp-request` operation from the mirror
        """
        raise NotImplementedError

    async def delete(self, data, ts):
        """
        Method to delete data.
        Handle the `delete` operation from the mirror
        """
        raise NotImplementedError

    async def update(self, data, ts):
        """
        Method to update data.
        Handle the `update` operation from the mirror
        """
        raise NotImplementedError

    async def get_ids_since_timestamp(self, data, ts):
        """
        Method to get ids list since given timestamp.
        Handle the `ids-since-timestamp-request` operation from the mirror
        """
        raise NotImplementedError
