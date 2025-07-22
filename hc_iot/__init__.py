"""Support for Hc Iot devices."""

import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SUPPORTED_PLATFORMS
from .hc_iot_sdk.manager import Manager, ManagerInitError

_LOGGER = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, hass_config: dict) -> bool:
    """Set up the Hc Iot Devices integration."""
    # Check for existing config entries for this integration
    hass.data.setdefault(DOMAIN, {})
    if not hass.config_entries.async_entries(DOMAIN):
        # No entries found, initiate the configuration flow
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hc Iot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # 初始化manager
    try:
        hass.data[DOMAIN][entry.entry_id] = {
            "manager": Manager(entry.entry_id, entry.data)
        }
    except ManagerInitError as e:
        _LOGGER.error("Manager initialization failed: %s", e)
        return False
    # 初始化平台
    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading the HC platforms."""
    manager: Manager = hass.data[DOMAIN][entry.entry_id]["manager"]
    if manager is not None:
        manager.unload()
    return True
