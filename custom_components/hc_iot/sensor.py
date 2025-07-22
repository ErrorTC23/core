"""Sensor platform for Hc IoT integration."""

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .hc_iot_sdk.manager import Manager, ManagerDevice, ManagerDeviceModel


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Hc sensors entry."""
    manager: Manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    if manager is not None:
        entities = []
        devices: list[ManagerDevice] = await manager.getSensorList()
        for device in devices:
            entities.extend(HcSensorEntity(device, model) for model in device.models)
        manager.sensor_list = entities
        async_add_entities(entities)
    return True


class HcSensorEntity(ManagerDevice, SensorEntity):
    """Hc Sensor Entity."""

    device: ManagerDevice
    model: ManagerDeviceModel
    value: Any

    def __init__(
        self,
        device: ManagerDevice,
        model: ManagerDeviceModel,
    ) -> None:
        """Init HcSensorEntity."""
        self.device = device
        self.model = model
        self.entity_description = SensorEntityDescription(
            key=model.type,
            name="",
            translation_key=model.type,
            device_class=model.device_class,
            unit_of_measurement=model.unit_of_measurement,
            suggested_display_precision=model.display_precision,
            state_class=model.state_class,
        )
        self._attr_unique_id = (
            f"{self.device.device_type}_{self.device.device_id}_{self.model.type}"
        )
        self._attr_name = model.name
        self.value = None

    def updateValue(self, value: Any | None = None) -> None:
        """Update the sensor state."""
        if value is not None:
            self.value = value
            if self.model.transfer is not None:
                for t in self.model.transfer:
                    if t.get("value") == self.value:
                        self.value = t.get("desc")
                        break
                self.schedule_update_ha_state()

    def updateStatus(self, status: Any | None = None) -> None:
        """Update the sensor state."""
        if status is not None:
            self.device.device_status = status
            self.schedule_update_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.device_id)},
            manufacturer=MANUFACTURER,
            name=self.device.device_name,
            model=self.device.device_type,
        )

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        return self.entity_description.unit_of_measurement

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.value

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self.device.device_status == 1
