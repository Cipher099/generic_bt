from __future__ import annotations

import asyncio
import dataclasses
import struct
from collections import namedtuple
from datetime import datetime
import logging

# from logging import Logger
from math import exp
from typing import Any, Callable, Tuple

from bleak.backends.scanner import (
    AdvertisementData,
)

_LOGGER = logging.getLogger(__name__)
HEADER_BYTES = b'\x1d\x02'
MSG_LENGTH = 17  # Adjust if needed

class BTScaleData:
    """
    Convert the device data into usable object for the visuals

    Have a look here: https://github.com/oliexdev/openScale/blob/master/android_app/app/src/main/java/com/health/openscale/core/bluetooth/BluetoothOneByoneNew.java#L32

    """

    def __init__(self, data: AdvertisementData):
        _LOGGER.debug("Manufacture Data: %s", data.manufacturer_data) # data to be decoded
        _LOGGER.debug("Platform Data: %s", data.platform_data)
        _LOGGER.debug("Service Data: %s", data.service_data)
        pass

    def _parse_scale_data(packet: bytes) -> float:
        if len(packet) != 17:
            raise ValueError("Unexpected packet length.")
    
        weight_bytes = packet[10:14]  # 4 bytes
        weight_dag = struct.unpack('<I', weight_bytes)[0]
        
        # Convert to kilograms (since 1 dag = 0.01 kg)
        return weight_dag * 0.01
    
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        height_m = height_cm / 100.0
        if height_m <= 0:
            raise ValueError("Height must be greater than zero")
        bmi = weight_kg / (height_m ** 2)
        return round(bmi, 2)
    
    

    def from_unsigned_int24_be(self, data):
        """Convert 3 bytes big-endian to int."""
        return (data[0] << 16) | (data[1] << 8) | data[2]

    def from_unsigned_int16_be(self, data):
        """Convert 2 bytes big-endian to int."""
        return (data[0] << 8) | data[1]

    def get_timestamp32(self, data, offset):
        """Decode a 32-bit timestamp, interpreted as seconds since Unix epoch."""
        timestamp = struct.unpack('>I', data[offset:offset + 4])[0]
        return datetime.utcfromtimestamp(timestamp)

    def parse_scale_packet(self, data):
        if not data:
            print("Received an empty message")
            return

        if len(data) < MSG_LENGTH:
            print("Message too short")
            return

        if not (data[0] == HEADER_BYTES[0] and data[1] == HEADER_BYTES[1]):
            print("Unrecognized message header")
            return

        msg_type = data[2]

        if msg_type == 0x00:
            # Historic measurement (skip real-time unless flagged)
            if data[7] != 0x80:
                print("Received real-time measurement, skipping.")
                return

            timestamp = self.get_timestamp32(data, 3)
            raw_weight = self.from_unsigned_int24_be(data[8:11]) & 0x03FFFF
            weight = raw_weight / 1000.0  # Scale to kg
            impedance = self.from_unsigned_int16_be(data[15:17])

            print(f"[Historic] Weight: {weight} kg, Impedance: {impedance}, Time: {timestamp}")
            return {
                "type": "historic",
                "weight_kg": weight,
                "impedance": impedance,
                "timestamp": timestamp
            }

        elif msg_type == 0x80:
            # Final real-time weight
            raw_weight = self.from_unsigned_int24_be(data[3:6]) & 0x03FFFF
            weight = raw_weight / 1000.0
            print(f"[Realtime] Weight: {weight} kg")
            return {
                "type": "realtime",
                "weight_kg": weight
            }

        elif msg_type == 0x01:
            # Impedance packet
            impedance = self.from_unsigned_int16_be(data[4:6])
            print(f"[Realtime] Impedance: {impedance}")
            return {
                "type": "impedance",
                "impedance": impedance
            }

        else:
            print("Unknown message type")
            return

    pass