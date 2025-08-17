from homeassistant.config_entries import ConfigEntry
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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the example BLE sensors."""
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    async_add_entities([
        BluetoothSensorEntity(SensorEntityDescription(
                key=ATTR_VISCERAL,
                translation_key="visceral_fat",
                suggested_display_precision=0,
            ),)
    ])


class BluetoothSensorEntity(PassiveBluetoothProcessorEntity, SensorEntity):
    """Representation of an example BLE sensor."""

    def __init__(self, entity_description: SensorEntityDescription):
        super().__init__(entity_description)

    @property
    def native_value(self) -> float | int | str | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
