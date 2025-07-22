"""Config flow for Hc Iot integration."""

import time

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    HTTP_HOST,
    HTTP_PASSWORD,
    HTTP_USERNAME,
    PROJECT_ID,
    WS_HOST,
    WS_PASSWORD,
    WS_USERNAME,
)
from .hc_iot_sdk.manager import Manager, ManagerInitError


# Configuration class that handles flow initiated by the user for Hc Iot integration
class HcIotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hc Iot."""

    # Use version 1 for the configuration flow
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        # Placeholder for error messages
        placeholders = {}
        #  优化：第一次打开流程后展示错误，不太友好，需要做判断和区分
        #  迭代：PROJECT_ID根据获取列表后自己选择 /e-server-user-service/company/pageList
        #  迭代：WS相关参数从接口拿，接口未提供
        try:
            manager = Manager(id="flow" + str(time.time()), data=user_input)
            await manager.validate()
            return self.async_create_entry(
                title=user_input.get(PROJECT_ID),
                data={
                    HTTP_HOST: user_input.get(HTTP_HOST),
                    HTTP_PASSWORD: user_input.get(HTTP_PASSWORD),
                    HTTP_USERNAME: user_input.get(HTTP_USERNAME),
                    PROJECT_ID: user_input.get(PROJECT_ID),
                    WS_HOST: user_input.get(WS_HOST),
                    WS_PASSWORD: user_input.get(WS_PASSWORD),
                    WS_USERNAME: user_input.get(WS_USERNAME),
                },
            )
        except ManagerInitError as e:
            placeholders["msg"] = str(e)
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(HTTP_HOST): str,
                        vol.Required(HTTP_USERNAME): str,
                        vol.Required(HTTP_PASSWORD): str,
                        vol.Required(WS_HOST): str,
                        vol.Required(WS_USERNAME): str,
                        vol.Required(WS_PASSWORD): str,
                        vol.Required(PROJECT_ID): str,
                    }
                ),
                errors={"base": "sys_error"},
                description_placeholders=placeholders,
            )
