"""generic bt device"""

from uuid import UUID
import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError


_LOGGER = logging.getLogger(__name__)

connected_devices = set() 
notify_uuid = "00001812-0000-1000-8000-00805f9b34fb"

class GenericBTDevice:
    """Generic BT Device Class"""
    def __init__(self, ble_device: str):
        self._ble_device = ble_device
        self._client_stack = AsyncExitStack()
        self._lock = asyncio.Lock()

    async def update(self):
        pass

    async def stop(self):
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

    # def update_from_advertisement(self, advertisement):
    #     _LOGGER.debug(advertisement, exc_info=True)
    #     print(advertisement)
    #     pass

    async def async_start(self, detection_callback, scanning_mode: str = "passive"):
        _LOGGER.debug(
            "Starting ScaleDataUpdateCoordinator for address: %s", self._ble_device
        )
        # https://bleak.readthedocs.io/en/latest/api/scanner.html
        self._client: BleakClient | None = BleakClient(
            address_or_ble_device=self._ble_device)
        self._scanner: BleakScanner | None = BleakScanner(
            service_uuids=self._ble_device,
            detection_callback=detection_callback,
            scanning_mode= scanning_mode)

        found = False

        while not found:
            device = await BleakScanner.find_device_by_address(self._ble_device)

            if device is None:
                # maybe asyncio.sleep() here for some seconds if you aren't in a hurry
                # asyncio.sleep(10)
                continue
            try:
                # await self._client.connect()
                _LOGGER.debug("connected to", device.address)
                await self._scanner.start()

                # Not sure
                # connected_devices.add(device.address)

                found = True

            except BleakError:
                # if failed to connect, this is a no-op, if failed to start notifications, it will disconnect
                await self._client.disconnect()
                # I'm not sure if manually disconnecting triggers disconnected_callback, (pretty easy to figure this out though)
                # if so, you will be getting disconnected_callback called twice
                # if not, you should call it here
                # self.disconnect_callback(self._client)

        pass
