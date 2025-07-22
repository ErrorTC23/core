"""Select platform for Hc IoT integration."""

from typing import Any

from homeassistant.components.select import SelectEntity
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
        devices: list[ManagerDevice] = await manager.getSelectList()
        for device in devices:
            entities.extend(
                HcSelectEntity(device, model, manager) for model in device.models
            )
        manager.select_list = entities
        async_add_entities(entities)
    return True


class HcSelectEntity(ManagerDevice, SelectEntity):
    """Hc Select Entity."""

    device: ManagerDevice
    model: ManagerDeviceModel
    manager: Manager

    def __init__(
        self, device: ManagerDevice, model: ManagerDeviceModel, manager: Manager
    ) -> None:
        """Init HcSensorEntity."""
        self.device = device
        self.model = model
        self.manager = manager
        self._attr_unique_id = (
            f"{self.device.device_type}_{self.device.device_id}_{self.model.type}"
        )
        self._attr_name = model.name
        self._attr_options = [
            item.get("name")
            for item in self.model.instruct.get("multipleControllerDtoList", [])
        ]

    def updateValue(self, value: str | None = None) -> None:
        """Update the sensor state."""
        if value is not None:
            for t in self.model.transfer:
                if t.get("value") == str(value):
                    self._attr_current_option = t.get("desc")
                    break
            self.schedule_update_ha_state()

    def updateStatus(self, status: Any | None = None) -> None:
        """Update the sensor state."""
        if status is not None:
            self.device.device_status = status
            self.schedule_update_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        for item in self.model.instruct.get("multipleControllerDtoList", []):
            if item.get("name") == option:
                await self.manager.instruction(
                    self.device.device_id, self.model.type, item.get("value")
                )

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
    def available(self) -> bool:
        """Return if the device is available."""
        return self.device.device_status == 1
