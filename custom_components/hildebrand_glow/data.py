"""Custom types for hildebrand_glow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import HildebrandGlowEnergyMonitorApiClient
    from .coordinator import HildebrandGlowEnergyMonitorDataUpdateCoordinator


type HildebrandGlowEnergyMonitorConfigEntry = ConfigEntry[HildebrandGlowEnergyMonitorData]


@dataclass
class HildebrandGlowEnergyMonitorData:
    """Data for hildebrand_glow."""

    client: HildebrandGlowEnergyMonitorApiClient
    coordinator: HildebrandGlowEnergyMonitorDataUpdateCoordinator
    integration: Integration
