from abc import ABC, abstractmethod


class Protocol:
    SIMPLE = 'simple'
    FULL = 'full'


class SimpleMirrorClient(ABC):
    """
    Abstract Class for the simple client realization
    """
    _protocol = Protocol.SIMPLE

    async def get_protocol(self, **kwargs):
        """
        Method to return _protocol.
        Handle the `protocol-request` operation from the mirror
        """
        return self._protocol

    @abstractmethod
    async def _save_timestamp(self, _id, ts):
        """
        Method to save timestamp
        """

    @abstractmethod
    async def get_initial_point(self, **kwargs):
        """
        Method to get _last_modified value from the last object.
        Handle the `init-point-request` operation from the mirror
        """

    @abstractmethod
    async def upsert(self, data, ts):
        """
        Method to upsert data.
        Handle the `upsert` operation from the mirror
        """

    @abstractmethod
    async def noop(self, data, ts):
        """
        Handle the `noop` operation from the mirror
        """

    @abstractmethod
    async def get_timestamp(self, **kwargs):
        """
        Method to get latest timestamp.
        Handle the `timestamp-request` operation from the mirror
        """


class FullMirrorClient(ABC):
    """
    Abstract Class for the full client realization
    """
    _protocol = Protocol.FULL

    async def get_protocol(self, **kwargs):
        """
        Method to return _protocol.
        Handle the `protocol-request` operation from the mirror
        """
        return self._protocol

    @abstractmethod
    async def _save_timestamp(self, _id, ts):
        """
        Method to save timestamp
        """

    @abstractmethod
    async def get_initial_point(self, **kwargs):
        """
        Method to get _last_modified value from the last object.
        Handle the `init-point-request` operation from the mirror
        """

    @abstractmethod
    async def upsert(self, data, ts):
        """
        Method to upsert data.
        Handle the `upsert` operation from the mirror
        """

    @abstractmethod
    async def noop(self, data, ts):
        """
        Handle the `noop` operation from the mirror
        """

    @abstractmethod
    async def delete(self, data, ts):
        """
        Method to delete data.
        Handle the `delete` operation from the mirror
        """

    @abstractmethod
    async def update(self, data, ts):
        """
        Method to update data.
        Handle the `update` operation from the mirror
        """

    @abstractmethod
    async def get_timestamp(self, **kwargs):
        """
        Method to get latest timestamp.
        Handle the `timestamp-request` operation from the mirror
        """

    @abstractmethod
    async def get_ids_since_timestamp(self, data, ts):
        """
        Method to get ids list since given timestamp.
        Handle the `ids-since-timestamp-request` operation from the mirror
        """
