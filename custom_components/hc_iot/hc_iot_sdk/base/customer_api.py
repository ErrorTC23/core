"""封装平台API."""

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__package__)


class CustomerApi:
    """Customer API for handling requests to the HC IoT platform."""

    def __init__(
        self,
        host: str = "",
        access_token: str = "",
        project_id: str = "",
        username: str = "",
        password: str = "",
    ) -> None:
        """Initialize the CustomerApi with host, ws_host, access_token, and project_id."""
        self.access_token = access_token
        self.host = host
        self.project_id = project_id
        self.username = username
        self.password = password

    def __generate_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "e-server-user": self.access_token,
            "token": "yunqi",
        }

    async def __request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        headers = self.__generate_headers()
        session = aiohttp.ClientSession()
        try:
            async with session.request(
                method=method,
                url=self.host + path,
                headers=headers,
                params=params,
                json=body,
            ) as response:
                if response.status == 401:
                    # 鉴权失败后重新登录
                    await self._set_token()
                    return await self.__request(method, path, params, body)
                if response.status == 200:
                    response_data = await response.json()
                    if isinstance(response_data, dict):
                        _LOGGER.debug(response_data)
                        return response_data
                    return {
                        "code": 500,
                        "message": "Unexpected response format",
                    }
        finally:
            await session.close()

    async def _get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self.__request("GET", path, params, None)

    async def _post(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.__request("POST", path, params, body)

    async def login(self) -> dict[str, Any] | None:
        """Login to the account and return token."""
        body = {
            "username": self.username,
            "password": self.password,
        }
        return await self._post("/e-server/login", None, body)

    async def _set_token(self) -> None:
        """Login to the account and return token."""
        data = await self.login()
        self.access_token = data.get("data")

    async def _page(self, url: str, params: dict[str, Any] | None = None, per_page=100):
        """分页查询."""
        if not params:
            params = {}
        page = 1
        res = []
        while True:
            params["pageNo"] = page
            params["pageSize"] = per_page
            data = await self._get(
                url,
                params=params,
            )
            if page == data.get("data").get("pages"):
                break
            res.extend(data.get("data").get("records", []))
            page += 1
        return res

    async def device_page(
        self, params: dict[str, Any] | None = None, per_page=100
    ) -> list[dict[str, Any]]:
        """分页查询设备."""
        return await self._page(
            f"/e-server-device-service/device/page/{self.project_id}", params, per_page
        )

    async def model_page(
        self, params: dict[str, Any] | None = None, per_page=100
    ) -> list[dict[str, Any]]:
        """分页查询物模型."""
        params["isUniversal"] = 0
        return await self._page(
            f"/e-server-device-service/physicalModel/page/{self.project_id}",
            params,
            per_page,
        )

    async def instruction(self, body: dict[str, Any] | None = None) -> None:
        """控制指令下发."""
        await self._post(
            f"/e-server-logtask-service/instruction/control/{self.project_id}",
            None,
            body,
        )
