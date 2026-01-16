"""Constants for the Trello integration."""

DOMAIN = "trello"

# Trello API
TRELLO_API_BASE = "https://api.trello.com/1"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_API_TOKEN = "api_token"
CONF_BOARDS = "boards"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 5
MIN_UPDATE_INTERVAL = 1
MAX_UPDATE_INTERVAL = 1440  # 24 hours
