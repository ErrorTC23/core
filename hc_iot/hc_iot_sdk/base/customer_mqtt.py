"""Base class for Mqtt client."""

import asyncio
from collections.abc import Callable
import logging
import threading
from typing import Any

from paho.mqtt.client import MQTT_ERR_SUCCESS, Client, MQTTv5

_LOGGER = logging.getLogger(__package__)


class CustomerMqtt:
    """Base class for Mqtt client."""

    topic: str | None = None
    _client_id: str
    _host: str
    _port: int
    _username: str | None
    _password: str | None
    _mqtt: Client | None
    _on_message: asyncio.Event
    _thread: threading.Thread | None

    def __init__(
        self,
        client_id: str,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        _on_message: Callable | None = None,
    ) -> None:
        """Initialize the Mqtt client config."""
        self._client_id = client_id
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._mqtt = None
        self._thread = None
        self._on_message = _on_message

    def is_connected(self) -> bool:
        """Check if the Mqtt client is connected."""
        if not self._mqtt:
            return False
        return self._mqtt.is_connected()

    def connect(self, topic: str | None = None) -> None:
        """Connect."""
        self.topic = topic
        if self._thread:
            return
        self._thread = threading.Thread(target=self.__loop_thread)
        self._thread.daemon = True
        self._thread.name = self._client_id
        self._thread.start()

    def unload(self) -> None:
        """结束进程."""
        self._mqtt.disconnect()
        self._thread.join()

    def subscribe(self) -> None:
        """Subscribe to a topic."""
        if not self._mqtt:
            _LOGGER.error("Mqtt is None, cannot subscribe")
            return
        if not self._mqtt.is_connected():
            _LOGGER.error("Mqtt is not connected, cannot subscribe")
            return
        result, mid = self._mqtt.subscribe(self.topic)
        if result == MQTT_ERR_SUCCESS:
            _LOGGER.info("Subscribed to topic: %s", self.topic)
        else:
            _LOGGER.error(
                "Failed to subscribe to topic: %s, result: %s, mid: %s",
                self.topic,
                result,
                mid,
            )

    def __loop_thread(self) -> None:
        _LOGGER.info("Mqtt start")
        self._mqtt = Client(client_id=self._client_id, protocol=MQTTv5)
        # Set mqtt config
        if self._username:
            self._mqtt.username_pw_set(username=self._username, password=self._password)

        self._mqtt.on_connect = self.__on_connect
        self._mqtt.on_disconnect = self.__on_disconnect
        self._mqtt.on_message = self._on_message
        self.__try_reconnect()
        self._mqtt.loop_forever()
        _LOGGER.info("Mqtt exit!")

    def __on_connect(self, client, user_data, flags, rc, props) -> None:
        if not self._mqtt:
            _LOGGER.error("__on_connect, but mqtt is None")
            return
        if not self._mqtt.is_connected():
            return
        _LOGGER.info("Mqtt connect success")
        self.subscribe()

    def __on_disconnect(
        self,
        client: Any | None = None,
        userdata: Any | None = None,
        disconnect_flags: Any | None = None,
        reason_code: Any | None = None,
        properties: Any | None = None,
    ) -> None:
        # 当flag=0为正常退出，其他情况尝试重新连接
        if disconnect_flags != 0:
            self.__try_reconnect()

    def __try_reconnect(self) -> None:
        try:
            result = self._mqtt.connect(
                host=self._host,
                port=self._port,
                clean_start=True,
                keepalive=60,
            )
            if result != MQTT_ERR_SUCCESS:
                _LOGGER.error("Mqtt connect failed, %s", result)
        except (TimeoutError, OSError) as error:
            _LOGGER.error("Mqtt connect error, %s", error)
