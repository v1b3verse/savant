"""Constants for the Savant integration."""

DOMAIN = "savant"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USER = "user"
CONF_PASSWORD = "password"
CONF_HOST_TOKEN = "host_token"
CONF_SECRET_KEY = "secret_key"
CONF_HOST_UID = "host_uid"
CONF_HOME_ID = "home_id"

DEFAULT_PORT = 5000

PLATFORMS = [
    "light",
    "climate",
    "cover",
    "fan",
    "lock",
    "scene",
    "sensor",
    "switch",
]
