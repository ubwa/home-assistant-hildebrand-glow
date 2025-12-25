"""Sensor platform for hildebrand_glow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.hildebrand_glow.const import DOMAIN, PARALLEL_UPDATES as PARALLEL_UPDATES
from homeassistant.helpers.device_registry import DeviceInfo

from .electricity import ENTITY_DESCRIPTIONS as ELECTRICITY_DESCRIPTIONS, HildebrandGlowElectricitySensor
from .gas import ENTITY_DESCRIPTIONS as GAS_DESCRIPTIONS, HildebrandGlowGasSensor
from .tariff import ENTITY_DESCRIPTIONS as TARIFF_DESCRIPTIONS, HildebrandGlowTariffSensor

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.data import HildebrandGlowEnergyMonitorConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HildebrandGlowEnergyMonitorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    entities: list = []

    # Get meters from coordinator data
    meters = coordinator.data.get("meters", {})

    for meter_id, meter_data in meters.items():
        # Create device info for this meter
        device_info = DeviceInfo(
            identifiers={(DOMAIN, meter_id)},
            name=meter_data.get("name", "Smart Meter"),
            manufacturer="Hildebrand Technology",
            model=meter_data.get("model", "Smart Meter"),
        )

        # Add electricity sensors if electricity is available
        if meter_data.get("has_electricity", False):
            entities.extend(
                HildebrandGlowElectricitySensor(
                    coordinator=coordinator,
                    entity_description=description,
                    meter_id=meter_id,
                    device_info=device_info,
                )
                for description in ELECTRICITY_DESCRIPTIONS
            )

            # Add electricity tariff sensors
            entities.extend(
                HildebrandGlowTariffSensor(
                    coordinator=coordinator,
                    entity_description=description,
                    meter_id=meter_id,
                    device_info=device_info,
                )
                for description in TARIFF_DESCRIPTIONS
                if description.energy_type == "electricity"
            )

        # Add gas sensors if gas is available
        if meter_data.get("has_gas", False):
            entities.extend(
                HildebrandGlowGasSensor(
                    coordinator=coordinator,
                    entity_description=description,
                    meter_id=meter_id,
                    device_info=device_info,
                )
                for description in GAS_DESCRIPTIONS
            )

            # Add gas tariff sensors
            entities.extend(
                HildebrandGlowTariffSensor(
                    coordinator=coordinator,
                    entity_description=description,
                    meter_id=meter_id,
                    device_info=device_info,
                )
                for description in TARIFF_DESCRIPTIONS
                if description.energy_type == "gas"
            )

    async_add_entities(entities)
