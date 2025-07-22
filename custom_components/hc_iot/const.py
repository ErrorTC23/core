"""Constants for the Hc Iot integration."""

from homeassistant.const import Platform

MANUFACTURER = "华聪数科"

DOMAIN = "hc_iot"

APP_VERSION = "0.0.1"

HC_IOT_SIGNAL_UPDATE_ENTITY = "hc_entry_update"

HTTP_HOST = "http_host"
HTTP_USERNAME = "http_username"
HTTP_PASSWORD = "http_password"
WS_HOST = "ws_host"
WS_USERNAME = "ws_username"
WS_PASSWORD = "ws_password"
PROJECT_ID = "project_id"
TOKEN = "access_token"

# List of platforms that support config entry
SUPPORTED_PLATFORMS = [
    # Platform.SWITCH,
    # Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.TEXT,
]
