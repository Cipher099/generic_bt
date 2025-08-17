from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    EntityCategory,
    UnitOfTemperature,
    EVENT_STATE_CHANGED,
)

from .const import DOMAIN


def sensor_update_to_bluetooth_data_update(parsed_data):
    """Convert a sensor update to a Bluetooth data update."""
    # This function must convert the parsed_data
    # from your library's update_method to a `PassiveBluetoothDataUpdate`
    # See the structure above
    return PassiveBluetoothDataUpdate(
        devices={},
        entity_descriptions={},
        entity_data={},
        entity_names={},
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    # device_type = config_entry.data.get("device_type", None)
    async_add_entities([BluetoothWeightEntity(config_entry.data)])
    async_add_entities([BluetoothVisceralFatEntity(config_entry.data)])


class GenericBluetoothEntity():
    def __init__(self, config, registry=None):
        self._registry = registry
        self._name = "Generic"
        self._weight = config.get("")
        self._viseral = config.get("")

    def device_name(self):
        return {
            "name": "Generic Bluetooth",
            "identifiers": {(DOMAIN, self._name)},
            "manufacturer": "Generic"
        }


class BluetoothWeightEntity(SensorEntity, GenericBluetoothEntity):

    def __init__(self, config):
        GenericBluetoothEntity.__init__(self, config)

    @property
    def has_entity_name(self):
        return True

    @property
    def unique_id(self):
        return self.temperature_sensor_unique_id()

    @property
    def device_info(self):
        return self.device_info()
    
    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property    
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        sensor_state = self.hass.states.get(self._weight_sensor) if self._weight_sensor is not None else None
        return float(sensor_state.state) if valid_sensor_state(sensor_state) else None

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._async_handle_event)

    @callback
    async def _async_handle_event(self, event):
        if event.data.get("entity_id") == self._temperature_sensor:
            self.async_write_ha_state()

class BluetoothBMIEntity(SensorEntity):
    pass
class BluetoothBodyFatRateEntity(SensorEntity):
    pass
class BluetoothMuscleMassEntity(SensorEntity):
    pass
class BluetoothVisceralFatEntity(SensorEntity, GenericBluetoothEntity):

    def __init__(self, config):
        GenericBluetoothEntity.__init__(self, config)

    @property
    def has_entity_name(self):
        return True

    @property
    def unique_id(self):
        return self.temperature_sensor_unique_id()

    @property
    def device_info(self):
        return self.device_info()
    
    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property    
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        sensor_state = self.hass.states.get(self._visceral_sensor) if self._temperature_sensor is not None else None
        return float(sensor_state.state) if valid_sensor_state(sensor_state) else None

    async def async_added_to_hass(self):
        self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._async_handle_event)

    @callback
    async def _async_handle_event(self, event):
        if event.data.get("entity_id") == self._temperature_sensor:
            self.async_write_ha_state()