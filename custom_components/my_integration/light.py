import logging  # noqa: D100

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the light entity from a config entry."""
    _LOGGER.info("配置条目数据: %s", entry.data)
    async_add_entities([MyLight(entry.data)])


class MyLight(LightEntity):
    """Custom light entity for My Integration."""

    def __init__(self, config: dict) -> None:
        """Initialize the light entity."""
        self._name = config["name"]
        self._is_on = False
        self._attr_unique_id = f"my_integration_light_{config['name']}"

    @property
    def name(self) -> str:
        """Return the name of the light."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return True if the light is on, False otherwise."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the light."""
        self._is_on = True
        await self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the light."""
        self._is_on = False
        await self.async_write_ha_state()
