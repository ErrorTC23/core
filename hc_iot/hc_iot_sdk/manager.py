"""sdk manager for hc_iot."""

import json
import logging
from typing import Any

from hc_iot.const import (
    HTTP_HOST,
    HTTP_PASSWORD,
    HTTP_USERNAME,
    PROJECT_ID,
    WS_HOST,
    WS_PASSWORD,
    WS_USERNAME,
)

from .base.customer_api import CustomerApi
from .base.customer_mqtt import CustomerMqtt

_LOGGER = logging.getLogger(__package__)


class ManagerInitError(Exception):
    """Exception raised when Manager initialization fails."""

    def __init__(self, message) -> None:
        """Initialize the error with a message."""
        super().__init__(message)
        self.message = message

    def __str__(self):
        """Return the error message."""
        return self.message


class Manager:
    """Manager for Hc Iot SDK."""

    _api = None
    _mqtt = None
    _mqtt_msg = None
    sensor_list = []
    select_list = []
    text_list = []

    def __init__(self, id, data: dict) -> None:
        """Initialize the manager with a configuration."""
        if (
            data
            and data.get(HTTP_HOST)
            and data.get(HTTP_USERNAME)
            and data.get(HTTP_PASSWORD)
            and data.get(PROJECT_ID)
            and data.get(WS_HOST)
            and data.get(WS_USERNAME)
            and data.get(WS_PASSWORD)
        ):
            # 初始化 API 客户端
            self._api = CustomerApi(
                host=data[HTTP_HOST],
                project_id=data[PROJECT_ID],
                username=data[HTTP_USERNAME],
                password=data[HTTP_PASSWORD],
            )
            # 初始化 MQTT 客户端
            ws = data.get(WS_HOST).split(":")
            host = ws[0]
            port = int(ws[1]) if len(ws) > 1 else 1883
            self._mqtt = CustomerMqtt(
                client_id="华聪HA-" + id,
                host=host,
                port=port,
                username=data.get(WS_USERNAME),
                password=data.get(WS_PASSWORD),
                _on_message=self._mqtt_msg,
            )
            # 订阅 MQTT 实时数据主题
            self._mqtt.connect(f"datacloud/{data.get(PROJECT_ID)}/realTime")
        else:
            raise ManagerInitError("数据参数不完整.")

    def _mqtt_msg(self, client, userdata, message) -> None:
        """Handle incoming MQTT messages."""
        _LOGGER.debug(
            "Message received on topic: %s, payload: %s",
            message.topic,
            json.loads(message.payload),
        )
        json_data = json.loads(message.payload)
        for entity in self.sensor_list + self.select_list + self.text_list:
            key = entity.device.mqtt_key
            if json_data.get(key) is not None:
                entity.updateValue(json_data.get(key).get(entity.model.type))
            if json_data.get("system") is not None:
                entity.updateStatus(json_data.get("system").get(key + "_status"))

    def unload(self) -> None:
        """Unload."""
        self._mqtt.unload()
        self.sensor_list = []
        self.select_list = []
        self.text_list = []

    async def validate(self) -> None:
        """Login to the API and return the access token."""
        auth_data = await self._api.login()
        if not auth_data or not auth_data.get("code") == 0:
            raise ManagerInitError(
                auth_data.get("message")
                if not auth_data.get("message")
                else "API验证失败."
            )
        self._api.access_token = auth_data.get("data")
        if not self._mqtt.is_connected():
            raise ManagerInitError(
                auth_data.get("message")
                if not auth_data.get("message")
                else "Mqtt验证失败."
            )

    async def instruction(self, deviceId: str, model_type: str, value: str) -> None:
        """控制指令下发."""
        body = {
            "deviceIds": [deviceId],
            "controlList": [{"field": model_type, "value": value}],
        }
        await self._api.instruction(body)

    async def getSensorList(self) -> list:
        """获取传感器列表."""
        res: list[ManagerDevice] = []
        #  换成接口 self._api.model_page()
        models = [
            {
                "name": "gf",
                "nickName": "光伏",
                "type": 0,
                "remark": "",
                "companyId": 48,
                "deviceTypeId": 300,
                "isUniverse": 0,
                "fieldList": [
                    {
                        "fieldName": "ep",
                        "dataType": "double",
                        "fieldRemark": "光伏发电量",
                        "remark": None,
                        "unit": "kWh",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "energy",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "p",
                        "dataType": "double",
                        "fieldRemark": "功率",
                        "remark": None,
                        "unit": "W",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "power",
                        "state_class": "measurement",
                        "display_precision": 3,
                    },
                ],
                "interfaceList": None,
            },
            {
                "name": "kt",
                "nickName": "空调面板（智精灵）",
                "type": 0,
                "remark": "",
                "companyId": 48,
                "deviceTypeId": 342,
                "isUniverse": 0,
                "fieldList": [
                    {
                        "fieldName": "centrerunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开中风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "currentwind",
                        "dataType": "double",
                        "fieldRemark": "风速当前挡位",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 1,
                        "transfer": {
                            "id": 29,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "风速当前挡位",
                            "transferDataList": [
                                {"desc": "低速", "value": "1"},
                                {"desc": "中速", "value": "2"},
                                {"desc": "高速", "value": "3"},
                            ],
                            "field": "currentwind",
                        },
                        "instruct": {
                            "id": 99,
                            "name": "风速当前档位",
                            "deviceTypeId": 342,
                            "field": "currentwind",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "低速", "value": "1"},
                                {"name": "中速", "value": "2"},
                                {"name": "高速", "value": "3"},
                            ],
                            "checkField": "currentwind",
                        },
                    },
                    {
                        "fieldName": "highrunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开高风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "keylock",
                        "dataType": "double",
                        "fieldRemark": "温控面板按键锁",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 30,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "温控面板按键锁",
                            "transferDataList": [
                                {"desc": "正常使用", "value": "0"},
                                {"desc": "半锁", "value": "1"},
                                {"desc": "四分之三锁", "value": "2"},
                                {"desc": "全锁", "value": "3"},
                            ],
                            "field": "keylock",
                        },
                        "instruct": {
                            "id": 100,
                            "name": "按键锁",
                            "deviceTypeId": 342,
                            "field": "keylock",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "正常使用", "value": "0"},
                                {"name": "半锁", "value": "1"},
                                {"name": "四分之三锁", "value": "2"},
                                {"name": "全锁", "value": "3"},
                            ],
                            "checkField": "keylock",
                        },
                    },
                    {
                        "fieldName": "lowercool",
                        "dataType": "double",
                        "fieldRemark": "制冷温度下限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "lowerheat",
                        "dataType": "double",
                        "fieldRemark": "制热温度下限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "lowrunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开低风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "mode",
                        "dataType": "double",
                        "fieldRemark": "模式设定",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 31,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "模式设定",
                            "transferDataList": [
                                {"desc": "内机制热", "value": "0"},
                                {"desc": "内机地暖同时制热", "value": "1"},
                                {"desc": "地暖制热", "value": "2"},
                                {"desc": "制冷模式", "value": "3"},
                                {"desc": "通风模式", "value": "9"},
                            ],
                            "field": "mode",
                        },
                        "instruct": {
                            "id": 101,
                            "name": "模式设定",
                            "deviceTypeId": 342,
                            "field": "mode",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "内机制热", "value": "0"},
                                {"name": "内机地暖同时制热", "value": "1"},
                                {"name": "地暖制热", "value": "2"},
                                {"name": "制冷模式", "value": "3"},
                                {"name": "通风模式", "value": "9"},
                            ],
                            "checkField": "mode",
                        },
                    },
                    {
                        "fieldName": "runningtime",
                        "dataType": "double",
                        "fieldRemark": "开阀累计运行时间",
                        "remark": None,
                        "unit": "小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "settingtemperature",
                        "dataType": "double",
                        "fieldRemark": "设定温度",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": {
                            "id": 104,
                            "name": "温度设定",
                            "deviceTypeId": 342,
                            "field": "settingtemperature",
                            "type": 0,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [],
                            "checkField": "",
                        },
                    },
                    {
                        "fieldName": "settingwind",
                        "dataType": "double",
                        "fieldRemark": "风速设定",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 32,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "风速设定",
                            "transferDataList": [
                                {"desc": "低速", "value": "1"},
                                {"desc": "中速", "value": "2"},
                                {"desc": "高速", "value": "3"},
                                {"desc": "自动", "value": "4"},
                            ],
                            "field": "settingwind",
                        },
                        "instruct": {
                            "id": 102,
                            "name": "风速设定",
                            "deviceTypeId": 342,
                            "field": "settingwind",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "低速", "value": "1"},
                                {"name": "中速", "value": "2"},
                                {"name": "高速", "value": "3"},
                                {"name": "自动", "value": "4"},
                            ],
                            "checkField": "settingwind",
                        },
                    },
                    {
                        "fieldName": "signal",
                        "dataType": "double",
                        "fieldRemark": "温控器接收网关的信号强度",
                        "remark": None,
                        "unit": "dBm",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "signal_strength",
                        "state_class": "measurement",
                        "display_precision": 0,
                    },
                    {
                        "fieldName": "status",
                        "dataType": "double",
                        "fieldRemark": "状态",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 1,
                        "transfer": {
                            "id": 33,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "状态",
                            "transferDataList": [
                                {"desc": "通讯正常", "value": "88"},
                                {"desc": "通讯不正常", "value": "44"},
                                {"desc": "没有配置", "value": "0"},
                            ],
                            "field": "status",
                        },
                        "instruct": None,
                    },
                    {
                        "fieldName": "switch",
                        "dataType": "double",
                        "fieldRemark": "开关机控制",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                    },
                    {
                        "fieldName": "temperature",
                        "dataType": "double",
                        "fieldRemark": "室内当前温度",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "uppercool",
                        "dataType": "double",
                        "fieldRemark": "制冷温度上限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "upperheat",
                        "dataType": "double",
                        "fieldRemark": "制热温度上限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "watervalve",
                        "dataType": "double",
                        "fieldRemark": "水阀状态",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                    },
                ],
                "interfaceList": None,
            },
        ]
        devices = await self._api.device_page()
        for model in models:
            deviceModels: list[ManagerDeviceModel] = []
            # 过滤没有控制的 model
            deviceModels.extend(
                ManagerDeviceModel(field)
                for field in model.get("fieldList", [])
                if (field.get("instruct")) is None and field.get("show") == 1
            )
            if deviceModels:
                res.extend(
                    ManagerDevice(device, deviceModels)
                    for device in devices
                    if device.get("deviceType") == model.get("name")
                )
        return res

    async def getSelectList(self) -> list:
        """获取选项列表."""
        res: list[ManagerDevice] = []
        #  换成接口 self._api.model_page()
        models = [
            {
                "name": "gf",
                "nickName": "光伏",
                "type": 0,
                "remark": "",
                "companyId": 48,
                "deviceTypeId": 300,
                "isUniverse": 0,
                "fieldList": [
                    {
                        "fieldName": "ep",
                        "dataType": "double",
                        "fieldRemark": "光伏发电量",
                        "remark": None,
                        "unit": "kWh",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "energy",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "p",
                        "dataType": "double",
                        "fieldRemark": "功率",
                        "remark": None,
                        "unit": "W",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "power",
                        "state_class": "measurement",
                        "display_precision": 3,
                    },
                ],
                "interfaceList": None,
            },
            {
                "name": "kt",
                "nickName": "空调面板（智精灵）",
                "type": 0,
                "remark": "",
                "companyId": 48,
                "deviceTypeId": 342,
                "isUniverse": 0,
                "fieldList": [
                    {
                        "fieldName": "centrerunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开中风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "currentwind",
                        "dataType": "double",
                        "fieldRemark": "风速当前挡位",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 1,
                        "transfer": {
                            "id": 29,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "风速当前挡位",
                            "transferDataList": [
                                {"desc": "低速", "value": "1"},
                                {"desc": "中速", "value": "2"},
                                {"desc": "高速", "value": "3"},
                                {"desc": "自动", "value": "0"},
                            ],
                            "field": "currentwind",
                        },
                        "instruct": {
                            "id": 99,
                            "name": "风速当前档位",
                            "deviceTypeId": 342,
                            "field": "currentwind",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "低速", "value": "1"},
                                {"name": "中速", "value": "2"},
                                {"name": "高速", "value": "3"},
                                {"name": "自动", "value": "0"},
                            ],
                            "checkField": "currentwind",
                        },
                    },
                    {
                        "fieldName": "highrunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开高风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "keylock",
                        "dataType": "double",
                        "fieldRemark": "温控面板按键锁",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 30,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "温控面板按键锁",
                            "transferDataList": [
                                {"desc": "正常使用", "value": "0"},
                                {"desc": "半锁", "value": "1"},
                                {"desc": "四分之三锁", "value": "2"},
                                {"desc": "全锁", "value": "3"},
                            ],
                            "field": "keylock",
                        },
                        "instruct": {
                            "id": 100,
                            "name": "按键锁",
                            "deviceTypeId": 342,
                            "field": "keylock",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "正常使用", "value": "0"},
                                {"name": "半锁", "value": "1"},
                                {"name": "四分之三锁", "value": "2"},
                                {"name": "全锁", "value": "3"},
                            ],
                            "checkField": "keylock",
                        },
                    },
                    {
                        "fieldName": "lowercool",
                        "dataType": "double",
                        "fieldRemark": "制冷温度下限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "lowerheat",
                        "dataType": "double",
                        "fieldRemark": "制热温度下限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "lowrunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开低风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "mode",
                        "dataType": "double",
                        "fieldRemark": "模式设定",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 31,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "模式设定",
                            "transferDataList": [
                                {"desc": "内机制热", "value": "0"},
                                {"desc": "内机地暖同时制热", "value": "1"},
                                {"desc": "地暖制热", "value": "2"},
                                {"desc": "制冷模式", "value": "3"},
                                {"desc": "通风模式", "value": "9"},
                            ],
                            "field": "mode",
                        },
                        "instruct": {
                            "id": 101,
                            "name": "模式设定",
                            "deviceTypeId": 342,
                            "field": "mode",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "内机制热", "value": "0"},
                                {"name": "内机地暖同时制热", "value": "1"},
                                {"name": "地暖制热", "value": "2"},
                                {"name": "制冷模式", "value": "3"},
                                {"name": "通风模式", "value": "9"},
                            ],
                            "checkField": "mode",
                        },
                    },
                    {
                        "fieldName": "runningtime",
                        "dataType": "double",
                        "fieldRemark": "开阀累计运行时间",
                        "remark": None,
                        "unit": "小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "settingtemperature",
                        "dataType": "double",
                        "fieldRemark": "设定温度",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": {
                            "id": 104,
                            "name": "温度设定",
                            "deviceTypeId": 342,
                            "field": "settingtemperature",
                            "type": 0,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [],
                            "checkField": "",
                        },
                    },
                    {
                        "fieldName": "settingwind",
                        "dataType": "double",
                        "fieldRemark": "风速设定",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 32,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "风速设定",
                            "transferDataList": [
                                {"desc": "低速", "value": "1"},
                                {"desc": "中速", "value": "2"},
                                {"desc": "高速", "value": "3"},
                                {"desc": "自动", "value": "4"},
                            ],
                            "field": "settingwind",
                        },
                        "instruct": {
                            "id": 102,
                            "name": "风速设定",
                            "deviceTypeId": 342,
                            "field": "settingwind",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "低速", "value": "1"},
                                {"name": "中速", "value": "2"},
                                {"name": "高速", "value": "3"},
                                {"name": "自动", "value": "4"},
                            ],
                            "checkField": "settingwind",
                        },
                    },
                    {
                        "fieldName": "signal",
                        "dataType": "double",
                        "fieldRemark": "温控器接收网关的信号强度",
                        "remark": None,
                        "unit": "dBm",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "signal_strength",
                        "state_class": "measurement",
                        "display_precision": 0,
                    },
                    {
                        "fieldName": "status",
                        "dataType": "double",
                        "fieldRemark": "状态",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 1,
                        "transfer": {
                            "id": 33,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "状态",
                            "transferDataList": [
                                {"desc": "通讯正常", "value": "88"},
                                {"desc": "通讯不正常", "value": "44"},
                                {"desc": "没有配置", "value": "0"},
                            ],
                            "field": "status",
                        },
                        "instruct": None,
                    },
                    {
                        "fieldName": "switch",
                        "dataType": "double",
                        "fieldRemark": "开关机控制",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                    },
                    {
                        "fieldName": "temperature",
                        "dataType": "double",
                        "fieldRemark": "室内当前温度",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "uppercool",
                        "dataType": "double",
                        "fieldRemark": "制冷温度上限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "upperheat",
                        "dataType": "double",
                        "fieldRemark": "制热温度上限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "watervalve",
                        "dataType": "double",
                        "fieldRemark": "水阀状态",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                    },
                ],
                "interfaceList": None,
            },
        ]
        devices = await self._api.device_page()
        for model in models:
            deviceModels: list[ManagerDeviceModel] = []
            # 过滤控制类型为2的model
            deviceModels.extend(
                ManagerDeviceModel(field)
                for field in model.get("fieldList", [])
                if (field.get("instruct")) is not None
                and field.get("instruct").get("type", -1) == 2
                and field.get("show") == 1
            )
            if deviceModels:
                res.extend(
                    ManagerDevice(device, deviceModels)
                    for device in devices
                    if device.get("deviceType") == model.get("name")
                )
        return res

    async def getTextList(self) -> list:
        """获取文字列表."""
        res: list[ManagerDevice] = []
        #  换成接口 self._api.model_page()
        models = [
            {
                "name": "gf",
                "nickName": "光伏",
                "type": 0,
                "remark": "",
                "companyId": 48,
                "deviceTypeId": 300,
                "isUniverse": 0,
                "fieldList": [
                    {
                        "fieldName": "ep",
                        "dataType": "double",
                        "fieldRemark": "光伏发电量",
                        "remark": None,
                        "unit": "kWh",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "energy",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "p",
                        "dataType": "double",
                        "fieldRemark": "功率",
                        "remark": None,
                        "unit": "W",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "power",
                        "state_class": "measurement",
                        "display_precision": 3,
                    },
                ],
                "interfaceList": None,
            },
            {
                "name": "kt",
                "nickName": "空调面板（智精灵）",
                "type": 0,
                "remark": "",
                "companyId": 48,
                "deviceTypeId": 342,
                "isUniverse": 0,
                "fieldList": [
                    {
                        "fieldName": "centrerunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开中风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "currentwind",
                        "dataType": "double",
                        "fieldRemark": "风速当前挡位",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 1,
                        "transfer": {
                            "id": 29,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "风速当前挡位",
                            "transferDataList": [
                                {"desc": "低速", "value": "1"},
                                {"desc": "中速", "value": "2"},
                                {"desc": "高速", "value": "3"},
                                {"desc": "自动", "value": "0"},
                            ],
                            "field": "currentwind",
                        },
                        "instruct": {
                            "id": 99,
                            "name": "风速当前档位",
                            "deviceTypeId": 342,
                            "field": "currentwind",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "低速", "value": "1"},
                                {"name": "中速", "value": "2"},
                                {"name": "高速", "value": "3"},
                                {"name": "自动", "value": "0"},
                            ],
                            "checkField": "currentwind",
                        },
                    },
                    {
                        "fieldName": "highrunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开高风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "keylock",
                        "dataType": "double",
                        "fieldRemark": "温控面板按键锁",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 30,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "温控面板按键锁",
                            "transferDataList": [
                                {"desc": "正常使用", "value": "0"},
                                {"desc": "半锁", "value": "1"},
                                {"desc": "四分之三锁", "value": "2"},
                                {"desc": "全锁", "value": "3"},
                            ],
                            "field": "keylock",
                        },
                        "instruct": {
                            "id": 100,
                            "name": "按键锁",
                            "deviceTypeId": 342,
                            "field": "keylock",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "正常使用", "value": "0"},
                                {"name": "半锁", "value": "1"},
                                {"name": "四分之三锁", "value": "2"},
                                {"name": "全锁", "value": "3"},
                            ],
                            "checkField": "keylock",
                        },
                    },
                    {
                        "fieldName": "lowercool",
                        "dataType": "double",
                        "fieldRemark": "制冷温度下限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "lowerheat",
                        "dataType": "double",
                        "fieldRemark": "制热温度下限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "lowrunningtime",
                        "dataType": "double",
                        "fieldRemark": "阀开低风速累计时间",
                        "remark": None,
                        "unit": "0.1小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "mode",
                        "dataType": "double",
                        "fieldRemark": "模式设定",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 31,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "模式设定",
                            "transferDataList": [
                                {"desc": "内机制热", "value": "0"},
                                {"desc": "内机地暖同时制热", "value": "1"},
                                {"desc": "地暖制热", "value": "2"},
                                {"desc": "制冷模式", "value": "3"},
                                {"desc": "通风模式", "value": "9"},
                            ],
                            "field": "mode",
                        },
                        "instruct": {
                            "id": 101,
                            "name": "模式设定",
                            "deviceTypeId": 342,
                            "field": "mode",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "内机制热", "value": "0"},
                                {"name": "内机地暖同时制热", "value": "1"},
                                {"name": "地暖制热", "value": "2"},
                                {"name": "制冷模式", "value": "3"},
                                {"name": "通风模式", "value": "9"},
                            ],
                            "checkField": "mode",
                        },
                    },
                    {
                        "fieldName": "runningtime",
                        "dataType": "double",
                        "fieldRemark": "开阀累计运行时间",
                        "remark": None,
                        "unit": "小时",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "duration",
                        "state_class": "total",
                        "display_precision": 1,
                    },
                    {
                        "fieldName": "settingtemperature",
                        "dataType": "double",
                        "fieldRemark": "设定温度",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": {
                            "id": 104,
                            "name": "温度设定",
                            "deviceTypeId": 342,
                            "field": "settingtemperature",
                            "type": 0,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [],
                            "checkField": "",
                        },
                    },
                    {
                        "fieldName": "settingwind",
                        "dataType": "double",
                        "fieldRemark": "风速设定",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": {
                            "id": 32,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "风速设定",
                            "transferDataList": [
                                {"desc": "低速", "value": "1"},
                                {"desc": "中速", "value": "2"},
                                {"desc": "高速", "value": "3"},
                                {"desc": "自动", "value": "4"},
                            ],
                            "field": "settingwind",
                        },
                        "instruct": {
                            "id": 102,
                            "name": "风速设定",
                            "deviceTypeId": 342,
                            "field": "settingwind",
                            "type": 2,
                            "switchDto": {"open": None, "close": None},
                            "multipleControllerDtoList": [
                                {"name": "低速", "value": "1"},
                                {"name": "中速", "value": "2"},
                                {"name": "高速", "value": "3"},
                                {"name": "自动", "value": "4"},
                            ],
                            "checkField": "settingwind",
                        },
                    },
                    {
                        "fieldName": "signal",
                        "dataType": "double",
                        "fieldRemark": "温控器接收网关的信号强度",
                        "remark": None,
                        "unit": "dBm",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "signal_strength",
                        "state_class": "measurement",
                        "display_precision": 0,
                    },
                    {
                        "fieldName": "status",
                        "dataType": "double",
                        "fieldRemark": "状态",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 1,
                        "transfer": {
                            "id": 33,
                            "typeId": 342,
                            "typeName": "空调面板（智精灵）",
                            "fieldName": "状态",
                            "transferDataList": [
                                {"desc": "通讯正常", "value": "88"},
                                {"desc": "通讯不正常", "value": "44"},
                                {"desc": "没有配置", "value": "0"},
                            ],
                            "field": "status",
                        },
                        "instruct": None,
                    },
                    {
                        "fieldName": "switch",
                        "dataType": "double",
                        "fieldRemark": "开关机控制",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                    },
                    {
                        "fieldName": "temperature",
                        "dataType": "double",
                        "fieldRemark": "室内当前温度",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 1,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "uppercool",
                        "dataType": "double",
                        "fieldRemark": "制冷温度上限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "upperheat",
                        "dataType": "double",
                        "fieldRemark": "制热温度上限设定",
                        "remark": None,
                        "unit": "℃",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                        "device_class": "temperature",
                        "state_class": "measurement",
                        "display_precision": 2,
                    },
                    {
                        "fieldName": "watervalve",
                        "dataType": "double",
                        "fieldRemark": "水阀状态",
                        "remark": None,
                        "unit": "",
                        "show": 1,
                        "select": 0,
                        "transfer": None,
                        "instruct": None,
                    },
                ],
                "interfaceList": None,
            },
        ]
        devices = await self._api.device_page()
        for model in models:
            deviceModels: list[ManagerDeviceModel] = []
            # 过滤控制类型为0的model
            deviceModels.extend(
                ManagerDeviceModel(field)
                for field in model.get("fieldList", [])
                if (field.get("instruct")) is not None
                and field.get("instruct").get("type", -1) == 0
                and field.get("show") == 1
            )
            if deviceModels:
                res.extend(
                    ManagerDevice(device, deviceModels)
                    for device in devices
                    if device.get("deviceType") == model.get("name")
                )
        return res


class ManagerDevice:
    """设备."""

    device_id: str
    device_name: str
    device_type: str
    device_status: int
    mqtt_key: str
    models: list

    def __init__(self, device_dict: dict[str, Any], models: list) -> None:
        """Init."""
        self.device_id = device_dict.get("id")
        self.device_name = device_dict.get("name")
        self.device_type = device_dict.get("deviceType")
        self.device_status = device_dict.get("status", 0)
        self.mqtt_key = f"{self.device_name}&{self.device_type}"
        self.models = models


class ManagerDeviceModel:
    """设备模型信息."""

    type: str
    name: str
    # 设备类型
    device_class: str
    # 测量类型
    state_class: str
    # 保留小数位数
    display_precision: int
    # 单位
    unit_of_measurement: str
    # 指令
    instruct: list
    # 展示转换(desc,value)
    transfer: list

    def __init__(self, model_dict: dict[str, Any]) -> None:
        """Init."""
        self.type = model_dict.get("fieldName")
        self.name = model_dict.get("fieldRemark")
        self.device_class = model_dict.get("device_class")
        self.state_class = model_dict.get("state_class")
        self.display_precision = model_dict.get("display_precision")
        self.unit_of_measurement = model_dict.get("unit", "")
        self.instruct = model_dict.get("instruct")
        self.transfer = (
            model_dict.get("transfer")["transferDataList"]
            if model_dict.get("transfer") is not None
            else []
        )
