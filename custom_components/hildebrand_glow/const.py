"""Constants for hildebrand_glow."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN = "hildebrand_glow"
ATTRIBUTION = "Data provided by Hildebrand Technology via Glowmarkt API"

# Platform parallel updates - applied to all platforms
PARALLEL_UPDATES = 1

# Glowmarkt API configuration
API_URL = "https://api.glowmarkt.com/api/v0-1"
APPLICATION_ID = "b0f1b774-a586-4f72-9edd-27ead8aa7a8d"

# Resource classifiers for energy data
CLASSIFIER_ELECTRICITY_CONSUMPTION = "electricity.consumption"
CLASSIFIER_ELECTRICITY_COST = "electricity.consumption.cost"
CLASSIFIER_GAS_CONSUMPTION = "gas.consumption"
CLASSIFIER_GAS_COST = "gas.consumption.cost"

# API period parameters for readings queries
PERIOD_DAY = "P1D"
PERIOD_WEEK = "P1W"
PERIOD_MONTH = "P1M"

# Update intervals (in minutes)
UPDATE_INTERVAL_DAILY = 5  # Poll daily data every 5 minutes
UPDATE_INTERVAL_HISTORICAL = 60  # Poll weekly/monthly data every hour

# Default configuration values
DEFAULT_UPDATE_INTERVAL_MINUTES = 5
DEFAULT_ENABLE_DEBUGGING = False
