"""Constants for Equation Virtus AC integration."""

DOMAIN = "equation_virtus_ac"

# API Configuration
BASE_URL = "https://enki.api.devportal.adeo.cloud"
API_KEY_AIRCO = "Nntj37xS5lih1qqFy8SbyHWKG5NEhSCm"
API_KEY_NODE = "UBb0Kv6xXpG6bOvD8VZ9A63uxqQ4G1A3"

# Keycloak Configuration
AUTH_URL = "https://keycloak-prod.iot.leroymerlin.fr/realms/enki"
TOKEN_URL = f"{AUTH_URL}/protocol/openid-connect/token"
CLIENT_ID = "enki-front"

# API Endpoints
ENDPOINT_CHECK_STATE = "/api-enki-equation-airco-prod/v1/equation-airco/{node_id}/check-airconditioner-state"
ENDPOINT_CHANGE_STATE = "/api-enki-equation-airco-prod/v1/equation-airco/{node_id}/change-airconditioner-state"
ENDPOINT_CHECK_ERROR = "/api-enki-equation-airco-prod/v1/equation-airco/{node_id}/check-airconditioner-error"
ENDPOINT_NODE_INFO = "/api-enki-node-agg-prod/v1/nodes/{node_id}"
ENDPOINT_DASHBOARD = "/api-enki-mobile-bff-prod/v1/dashboard/homes/{home_id}"

# Configuration keys
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_HOME_ID = "home_id"
CONF_NODE_ID = "node_id"
CONF_DEVICE_NAME = "device_name"
CONF_TOKEN_EXPIRES = "token_expires"

# Operating modes
HVAC_MODE_COOL = "COOL"
HVAC_MODE_HEAT = "HEAT"
HVAC_MODE_FAN = "FAN"
HVAC_MODE_DRY = "DRY"
HVAC_MODE_AUTO = "AUTO"

# Fan speeds
FAN_LOW = "LOW"
FAN_MEDIUM = "MEDIUM"
FAN_HIGH = "HIGH"
FAN_AUTO = "AUTO"

# Power states
POWER_ON = "ON"
POWER_OFF = "OFF"

# Polling interval (seconds)
SCAN_INTERVAL = 30

# Temperature limits
MIN_TEMP = 16
MAX_TEMP = 30
