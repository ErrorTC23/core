"""Config flow for My Integration."""

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


class MyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """配置流类，用于引导用户配置 My Integration 集成。
    负责处理用户输入（如设备名称、IP），并创建对应的配置条目。.
    """  # noqa: D205

    async def async_step_user(self, user_input=None):
        """处理用户配置的核心步骤：
        - 如果用户提交了 `user_input`（包含 `name` 和 `ip`），则创建配置条目；
        - 如果未提交，则展示输入表单，要求用户填写 `name` 和 `ip`。.
        """  # noqa: D205
        if user_input:
            return self.async_create_entry(title="My Device", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("name"): str, vol.Required("ip"): str}
            ),
        )
