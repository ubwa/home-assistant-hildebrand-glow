"""Number platform for hildebrand_glow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.hildebrand_glow.const import PARALLEL_UPDATES as PARALLEL_UPDATES
from homeassistant.components.number import NumberEntityDescription

from .target_humidity import ENTITY_DESCRIPTIONS as HUMIDITY_DESCRIPTIONS, HildebrandGlowEnergyMonitorHumidityNumber

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.data import HildebrandGlowEnergyMonitorConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[NumberEntityDescription, ...] = (*HUMIDITY_DESCRIPTIONS,)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HildebrandGlowEnergyMonitorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    async_add_entities(
        HildebrandGlowEnergyMonitorHumidityNumber(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in HUMIDITY_DESCRIPTIONS
    )
