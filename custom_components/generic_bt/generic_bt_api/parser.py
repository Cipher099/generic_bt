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
HEIGHT = 171 # in cmm (temporary)
SEX=1
PEOPLE_TYPE=1
AGE=38


class BTScaleData:
    """
    Convert the device data into usable object for the visuals

    Have a look here: https://github.com/oliexdev/openScale/blob/master/android_app/app/src/main/java/com/health/openscale/core/bluetooth/BluetoothOneByoneNew.java#L32

    """
    weight: str = "0"
    impedance: str = "0"
    timestamp: str = "0"

    calculation_object: OneByoneNewLib | None

    def __init__(self, data: AdvertisementData):
        _LOGGER.debug("Manufacture Data: %s", data.manufacturer_data) # data to be decoded
        _LOGGER.debug("Platform Data: %s", data.platform_data)
        _LOGGER.debug("Service Data: %s", data.service_data)
        self.calculation_object = OneByoneNewLib(sex=SEX, age=AGE, height=HEIGHT, people_type=PEOPLE_TYPE)
        byte_data = list(data.manufacturer_data.values())[0]
        self.parse_scale_packet(data_bytes=byte_data)

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

    # def from_unsigned_int16_be(self, data):
    #     """Convert 2 bytes big-endian to int."""
    #     return (data[0] << 8) | data[1]
    
    def from_unsigned_int16_be(self, data: bytes, offset: int) -> int:
        return int.from_bytes(data[offset:offset+2], byteorder='big', signed=False)

    def get_timestamp32(self, data, offset):
        """Decode a 32-bit timestamp, interpreted as seconds since Unix epoch."""
        timestamp = struct.unpack('>I', data[offset:offset + 4])[0]
        return datetime.utcfromtimestamp(timestamp)

    def parse_scale_packet(self, data_bytes: bytearray):
        if not data_bytes:
            _LOGGER.debug("Received an empty message")
            return

        _LOGGER.debug("Data: %r", data_bytes)

        weight_raw = data_bytes[9] + (data_bytes[10] << 8)

        weight_kg = weight_raw / 100  # assuming scale uses 0.1kg units
        weight_lb = weight_raw / 100 * 2.20462
        impedance_raw = self.from_unsigned_int16_be(data=data_bytes, offset=4)

        unit_flag = data_bytes[15]
        unit = "kg" if unit_flag == 1 else "lb"

        self.raw_weight = weight_raw
        self.weight_kg = weight_kg
        self.impedance = impedance_raw
        self.bmi = self.calculation_object.get_bmi(weight_raw)
        self.bmmr = self.calculation_object.get_bmmr(weight=weight_kg)
        self.fat_percentage  = self.calculation_object.get_body_fat_percentage(weight=weight_kg, impedance=impedance_raw)
        self.bone_mass = self.calculation_object.get_bone_mass(weight=weight_kg, impedance=impedance_raw)
        self.muscle_mass = self.calculation_object.get_muscle_mass(weight=weight_kg, impedance=impedance_raw)
        self.skeletal_mass = self.calculation_object.get_skeleton_muscle_percentage(weight=weight_kg, impedance=impedance_raw)
        self.visceral = self.calculation_object.get_visceral_fat(weight=weight_kg)
        self.water_percentage = self.calculation_object.get_water_percentage(weight=weight_kg, impedance=impedance_raw)
        self.protein_percentage = self.calculation_object.get_protein_percentage(weight=weight_kg, impedance=impedance_raw)
        self.weight_lb = weight_lb
        self.unit_flag = unit_flag
        self.unit_guess = unit
        self.full_bytes = list(data_bytes)
        
    def __str__(self):
        return "Weight: %s, Raw: %s", self.weight_kg, self.raw_weight

    pass

class OneByoneNewLib:
    def __init__(self, sex: int, age: int, height: float, people_type: int):
        self.sex = sex  # 0 = female, 1 = male
        self.age = age
        self.height = height  # in cm
        self.people_type = people_type  # 0 = low, 1 = medium, 2 = high activity

    def get_bmi(self, weight: float) -> float:
        bmi = weight / ((self.height / 100) ** 2)
        return self._get_bounded(bmi, 10, 90)

    def get_lbm(self, weight: float, impedance: int) -> float:
        lbm_coeff = ((self.height / 100) ** 2) * 9.058
        lbm_coeff += 12.226
        lbm_coeff += weight * 0.32
        lbm_coeff -= impedance * 0.0068
        lbm_coeff -= self.age * 0.0542
        return lbm_coeff

    def get_bmmr_coeff(self, weight: float) -> float:
        bmmr_coeff = 20
        if self.sex == 1:
            bmmr_coeff = 21
            if self.age < 13:
                bmmr_coeff = 36
            elif self.age < 16:
                bmmr_coeff = 30
            elif self.age < 18:
                bmmr_coeff = 26
            elif self.age < 30:
                bmmr_coeff = 23
            elif self.age >= 50:
                bmmr_coeff = 20
        else:
            if self.age < 13:
                bmmr_coeff = 34
            elif self.age < 16:
                bmmr_coeff = 29
            elif self.age < 18:
                bmmr_coeff = 24
            elif self.age < 30:
                bmmr_coeff = 22
            elif self.age >= 50:
                bmmr_coeff = 19
        return bmmr_coeff

    def get_bmmr(self, weight: float) -> float:
        if self.sex == 1:
            bmmr = weight * 14.916 + 877.8 - self.height * 0.726 - self.age * 8.976
        else:
            bmmr = weight * 10.2036 + 864.6 - self.height * 0.39336 - self.age * 6.204
        return self._get_bounded(bmmr, 500, 1000)

    def get_body_fat_percentage(self, weight: float, impedance: int) -> float:
        body_fat = self.get_lbm(weight, impedance)

        if self.sex == 0:
            body_fat_const = 9.25 if self.age < 50 else 7.25
        else:
            body_fat_const = 0.8

        body_fat -= body_fat_const

        if self.sex == 0:
            if weight < 50:
                body_fat *= 1.02
            elif weight > 60:
                body_fat *= 0.96
            if self.height > 160:
                body_fat *= 1.03
        else:
            if weight < 61:
                body_fat *= 0.98

        return 100 * (1 - body_fat / weight)

    def get_bone_mass(self, weight: float, impedance: int) -> float:
        lbm_coeff = self.get_lbm(weight, impedance)
        bone_mass_const = 0.18016894 if self.sex == 1 else 0.245691014
        bone_mass_const = lbm_coeff * 0.05158 - bone_mass_const

        if bone_mass_const <= 2.2:
            bone_mass = bone_mass_const - 0.1
        else:
            bone_mass = bone_mass_const + 0.1

        return self._get_bounded(bone_mass, 0.5, 8)

    def get_muscle_mass(self, weight: float, impedance: int) -> float:
        muscle_mass = weight - self.get_body_fat_percentage(weight, impedance) / 100 * weight
        muscle_mass -= self.get_bone_mass(weight, impedance)
        return self._get_bounded(muscle_mass, 10, 120)

    def get_skeleton_muscle_percentage(self, weight: float, impedance: int) -> float:
        skeleton_muscle_mass = self.get_water_percentage(weight, impedance)
        skeleton_muscle_mass *= weight * 0.8422 * 0.01
        skeleton_muscle_mass -= 2.9903
        skeleton_muscle_mass /= weight
        return skeleton_muscle_mass * 100

    def get_visceral_fat(self, weight: float) -> float:
        if self.sex == 1:
            if self.height < weight * 1.6 + 63.0:
                visceral_fat = self.age * 0.15 + ((weight * 305.0) /
                    ((self.height * 0.0826 * self.height - self.height * 0.4) + 48.0)) - 2.9
            else:
                visceral_fat = self.age * 0.15 + (weight * (self.height * -0.0015 + 0.765) - self.height * 0.143) - 5.0
        else:
            if weight <= self.height * 0.5 - 13.0:
                visceral_fat = self.age * 0.07 + (weight * (self.height * -0.0024 + 0.691) - self.height * 0.027) - 10.5
            else:
                visceral_fat = self.age * 0.07 + ((weight * 500.0) /
                    ((self.height * 1.45 + self.height * 0.1158 * self.height) - 120.0)) - 6.0

        return self._get_bounded(visceral_fat, 1, 50)

    def get_water_percentage(self, weight: float, impedance: int) -> float:
        water_percentage = (100 - self.get_body_fat_percentage(weight, impedance)) * 0.7
        if water_percentage > 50:
            water_percentage *= 0.98
        else:
            water_percentage *= 1.02

        return self._get_bounded(water_percentage, 35, 75)

    def get_protein_percentage(self, weight: float, impedance: int) -> float:
        body_fat = self.get_body_fat_percentage(weight, impedance)
        water = self.get_water_percentage(weight, impedance)
        bone_mass = self.get_bone_mass(weight, impedance)
        return (100.0 - body_fat - water * 1.08) - (bone_mass / weight) * 100.0

    def _get_bounded(self, value: float, lower_bound: float, upper_bound: float) -> float:
        return max(lower_bound, min(upper_bound, value))
