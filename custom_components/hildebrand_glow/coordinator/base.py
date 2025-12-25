"""
Core DataUpdateCoordinator implementation for hildebrand_glow.

This module contains the main coordinator class that manages data fetching
and updates for all entities in the integration. It handles refresh cycles,
error handling, pence-to-GBP conversion, and triggers reauthentication when needed.

For more information on coordinators:
https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from custom_components.hildebrand_glow.api import (
    HildebrandGlowEnergyMonitorApiClientAuthenticationError,
    HildebrandGlowEnergyMonitorApiClientError,
)
from custom_components.hildebrand_glow.const import (
    CLASSIFIER_ELECTRICITY_CONSUMPTION,
    CLASSIFIER_ELECTRICITY_COST,
    CLASSIFIER_GAS_CONSUMPTION,
    CLASSIFIER_GAS_COST,
    LOGGER,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.data import HildebrandGlowEnergyMonitorConfigEntry


class HildebrandGlowEnergyMonitorDataUpdateCoordinator(DataUpdateCoordinator):
    """
    Class to manage fetching data from the Glowmarkt API.

    This coordinator handles all data fetching for the integration and distributes
    updates to all entities. It manages:
    - Periodic data updates based on update_interval
    - Error handling and recovery
    - Authentication failure detection and reauthentication triggers
    - Pence-to-GBP conversion for cost data
    - Data distribution to all entities

    Attributes:
        config_entry: The config entry for this integration instance.
    """

    config_entry: HildebrandGlowEnergyMonitorConfigEntry

    async def _async_setup(self) -> None:
        """
        Set up the coordinator.

        This method is called automatically during async_config_entry_first_refresh()
        and is the ideal place for one-time initialization tasks.
        """
        LOGGER.debug("Coordinator setup complete for %s", self.config_entry.entry_id)

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Fetch data from API endpoint and transform for entities.

        This fetches all energy data from the Glowmarkt API and transforms it
        into a structure that's easy for entities to consume.

        Returns:
            Transformed data dictionary with:
            - meters: Dict of meter_id -> meter data
            - Each meter contains electricity/gas usage, cost, tariff info

        Raises:
            ConfigEntryAuthFailed: If authentication fails, triggers reauthentication.
            UpdateFailed: If data fetching fails for other reasons.
        """
        try:
            raw_data = await self.config_entry.runtime_data.client.async_get_data()
            return self._transform_data(raw_data)
        except HildebrandGlowEnergyMonitorApiClientAuthenticationError as exception:
            LOGGER.warning("Authentication error - %s", exception)
            raise ConfigEntryAuthFailed(
                translation_domain="hildebrand_glow",
                translation_key="authentication_failed",
            ) from exception
        except HildebrandGlowEnergyMonitorApiClientError as exception:
            LOGGER.exception("Error communicating with API")
            raise UpdateFailed(
                translation_domain="hildebrand_glow",
                translation_key="update_failed",
            ) from exception

    def _transform_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform raw API data into entity-friendly format.

        Converts pence to GBP and structures data for easy entity access.

        Args:
            raw_data: Raw data from the API client.

        Returns:
            Transformed data dictionary.
        """
        transformed: dict[str, Any] = {
            "meters": {},
        }

        meters = raw_data.get("meters", {})

        for meter_id, meter_data in meters.items():
            ve = meter_data.get("virtual_entity", {})
            readings = meter_data.get("readings", {})
            tariffs = meter_data.get("tariffs", {})
            resources = meter_data.get("resources", [])

            # Determine what types of meters are available
            has_electricity = any(r.get("classifier", "").startswith("electricity") for r in resources)
            has_gas = any(r.get("classifier", "").startswith("gas") for r in resources)

            # Build model string based on available meters
            if has_electricity and has_gas:
                model = "Electricity & Gas Smart Meter"
            elif has_electricity:
                model = "Electricity Smart Meter"
            elif has_gas:
                model = "Gas Smart Meter"
            else:
                model = "Smart Meter"

            meter_transformed: dict[str, Any] = {
                "meter_id": meter_id,
                "name": ve.get("name", "Smart Meter"),
                "postal_code": ve.get("postalCode"),
                "model": model,
                "has_electricity": has_electricity,
                "has_gas": has_gas,
                # Electricity data
                "electricity_usage_today": self._extract_reading_value(
                    readings.get(f"{CLASSIFIER_ELECTRICITY_CONSUMPTION}_today")
                ),
                "electricity_usage_week": self._extract_reading_value(
                    readings.get(f"{CLASSIFIER_ELECTRICITY_CONSUMPTION}_week")
                ),
                "electricity_usage_month": self._extract_reading_value(
                    readings.get(f"{CLASSIFIER_ELECTRICITY_CONSUMPTION}_month")
                ),
                "electricity_cost_today": self._pence_to_gbp(
                    self._extract_reading_value(readings.get(f"{CLASSIFIER_ELECTRICITY_COST}_today"))
                ),
                "electricity_cost_week": self._pence_to_gbp(
                    self._extract_reading_value(readings.get(f"{CLASSIFIER_ELECTRICITY_COST}_week"))
                ),
                "electricity_cost_month": self._pence_to_gbp(
                    self._extract_reading_value(readings.get(f"{CLASSIFIER_ELECTRICITY_COST}_month"))
                ),
                # Gas data
                "gas_usage_today": self._extract_reading_value(readings.get(f"{CLASSIFIER_GAS_CONSUMPTION}_today")),
                "gas_usage_week": self._extract_reading_value(readings.get(f"{CLASSIFIER_GAS_CONSUMPTION}_week")),
                "gas_usage_month": self._extract_reading_value(readings.get(f"{CLASSIFIER_GAS_CONSUMPTION}_month")),
                "gas_cost_today": self._pence_to_gbp(
                    self._extract_reading_value(readings.get(f"{CLASSIFIER_GAS_COST}_today"))
                ),
                "gas_cost_week": self._pence_to_gbp(
                    self._extract_reading_value(readings.get(f"{CLASSIFIER_GAS_COST}_week"))
                ),
                "gas_cost_month": self._pence_to_gbp(
                    self._extract_reading_value(readings.get(f"{CLASSIFIER_GAS_COST}_month"))
                ),
                # Tariff data (convert pence to GBP for standing charge)
                "electricity_rate": self._extract_tariff_rate(tariffs.get(CLASSIFIER_ELECTRICITY_CONSUMPTION)),
                "electricity_standing_charge": self._pence_to_gbp(
                    self._extract_standing_charge(tariffs.get(CLASSIFIER_ELECTRICITY_CONSUMPTION))
                ),
                "gas_rate": self._extract_tariff_rate(tariffs.get(CLASSIFIER_GAS_CONSUMPTION)),
                "gas_standing_charge": self._pence_to_gbp(
                    self._extract_standing_charge(tariffs.get(CLASSIFIER_GAS_CONSUMPTION))
                ),
            }

            transformed["meters"][meter_id] = meter_transformed

        return transformed

    def _extract_reading_value(self, reading_data: dict[str, Any] | None) -> float | None:
        """
        Extract the total value from a readings response.

        Args:
            reading_data: The readings response from the API.

        Returns:
            The sum of all reading values, or None if unavailable.
        """
        if not reading_data:
            return None

        data = reading_data.get("data", [])
        if not data:
            return None

        # Sum all values in the data array (each item is [timestamp, value])
        total = sum(item[1] for item in data if len(item) >= 2 and item[1] is not None)
        return round(total, 3)

    def _pence_to_gbp(self, pence: float | None) -> float | None:
        """
        Convert pence to GBP with 2 decimal places.

        Args:
            pence: Amount in pence.

        Returns:
            Amount in GBP, or None if input is None.
        """
        if pence is None:
            return None
        return round(pence / 100.0, 2)

    def _extract_tariff_rate(self, tariff_data: dict[str, Any] | None) -> float | None:
        """
        Extract the tariff rate from tariff response.

        Args:
            tariff_data: The tariff response from the API.

        Returns:
            The rate in pence per kWh, or None if unavailable.
        """
        if not tariff_data:
            return None

        data = tariff_data.get("data", [])
        if not data:
            return None

        # Get the first (most recent) tariff
        current_rates = data[0].get("currentRates", {}) if data else {}
        rate = current_rates.get("rate")
        return round(rate, 4) if rate is not None else None

    def _extract_standing_charge(self, tariff_data: dict[str, Any] | None) -> float | None:
        """
        Extract the standing charge from tariff response.

        Args:
            tariff_data: The tariff response from the API.

        Returns:
            The standing charge in pence per day, or None if unavailable.
        """
        if not tariff_data:
            return None

        data = tariff_data.get("data", [])
        if not data:
            return None

        current_rates = data[0].get("currentRates", {}) if data else {}
        charge = current_rates.get("standingCharge")
        return round(charge, 2) if charge is not None else None
