"""generic bt device"""

from uuid import UUID
import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from bleak.backends.scanner import (
    AdvertisementData,
    AdvertisementDataCallback,
    )


_LOGGER = logging.getLogger(__name__)

connected_devices = set() 
notify_uuid = ["00001812-0000-1000-8000-00805f9b34fb", "00001812-0000-1000-8000-00805f9b34fb"]

class GenericBTDevice:
    """Generic BT Device Class"""
    def __init__(self, ble_device: str):
        self._ble_device = ble_device
        self._client_stack = AsyncExitStack()
        self._lock = asyncio.Lock()

    async def update(self):
        """ Attempt to connect to the device? """
        self._client = BleakClient(
            address_or_ble_device=self._ble_device)
        pass

    async def stop(self):
        """ stop device from scanning """
        _LOGGER.debug("Stopping device")

    async def async_stop(self):
        """ stop device from scanning """
        _LOGGER.debug("async Stopping device")
        pass

    @property
    def connected(self):
        return not self._client is None

    async def get_client(self):
        async with self._lock:
            if not self._client:
                _LOGGER.debug("Connecting")
                try:
                    self._client = await self._client_stack.enter_async_context(BleakClient(self._ble_device, timeout=30))
                except asyncio.TimeoutError as exc:
                    _LOGGER.debug("Timeout on connect", exc_info=True)
                    # raise IdealLedTimeout("Timeout on connect") from exc
                except BleakError as exc:
                    _LOGGER.debug("Error on connect", exc_info=True)
                    # raise IdealLedBleakError("Error on connect") from exc
            else:
                _LOGGER.debug("Connection reused")

    async def write_gatt(self, target_uuid, data):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data_as_bytes = bytearray.fromhex(data)
        await self._client.write_gatt_char(uuid, data_as_bytes, True)

    async def read_gatt(self, target_uuid):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data = await self._client.read_gatt_char(uuid)
        print(data)
        return data

    async def async_start(self, detection_callback: AdvertisementDataCallback, scanning_mode: str = "passive"):
        _LOGGER.debug(
            "Device Starting ScaleDataUpdateCoordinator for address: %s", self._ble_device
        )
        # https://bleak.readthedocs.io/en/latest/api/scanner.html
        self._client = BleakClient(
            address_or_ble_device=self._ble_device)
        self._scanner = BleakScanner(
            service_uuids=notify_uuid,
            detection_callback=detection_callback,
            scanning_mode=scanning_mode)
        try:
            stop_event = asyncio.Event()

            _LOGGER.debug("Scanning for Device(s)")
            await self._scanner.start()
            await stop_event.wait()

        except BleakError as bleakError:
            # if failed to connect, this is a no-op, if failed to start notifications, it will disconnect
            await self._client.disconnect()
            await self._scanner.stop()
            # I'm not sure if manually disconnecting triggers disconnected_callback, (pretty easy to figure this out though)
            # if so, you will be getting disconnected_callback called twice
            # if not, you should call it here
                # self.disconnect_callback(self._client)
            _LOGGER.debug(bleakError)

        pass
