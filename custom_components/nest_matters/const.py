"""Constants for the Nest Matters integration."""
from homeassistant.const import Platform

DOMAIN = "nest_matters"
PLATFORMS = [Platform.CLIMATE]

# Configuration keys
CONF_MATTER_ENTITY = "matter_entity"
CONF_GOOGLE_ENTITY = "google_entity"
CONF_NAME = "name"

# Default routing preferences
DEFAULT_TEMP_SOURCE = "matter"  # Use Matter for temperature control (avoid rate limits)
DEFAULT_MODE_SOURCE = "google"  # Use Google for HVAC modes (full features)
DEFAULT_FAN_SOURCE = "google"   # Use Google for fan control

# Integration info
INTEGRATION_TITLE = "Nest Matters"
INTEGRATION_DESCRIPTION = "Combines Google Nest and Matter thermostat entities"