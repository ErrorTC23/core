import logging  # noqa: D100

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant  # 新增 HomeAssistant 类型导入

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # 显式标注 hass 类型
    entry: ConfigEntry,
    async_add_entities,
) -> None:  # 明确返回类型为 None
    """Set up the light entity from a config entry."""
    _LOGGER.info("配置条目数据: %s", entry.data)
    async_add_entities([MyLight(entry.data)])  # 加载灯实体


class MyLight(LightEntity):
    """Custom light entity for My Integration."""

    def __init__(self, config: dict) -> None:  # 显式标注返回类型为 None
        """Initialize the light entity."""
        self._name = config["name"]
        self._is_on = False

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
        await (
            self.async_write_ha_state()
        )  # 注意：async_write_ha_state 是异步方法，需用 await

    async def async_turn_off(self, **kwargs) -> None:  # 标注返回类型为 None
        """Turn off the light."""
        self._is_on = False
        await (
            self.async_write_ha_state()
        )  # 注意：async_write_ha_state 是异步方法，需用 await
