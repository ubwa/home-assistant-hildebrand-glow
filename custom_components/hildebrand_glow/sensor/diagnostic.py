"""Diagnostic sensors for hildebrand_glow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from custom_components.hildebrand_glow.entity import HildebrandGlowEnergyMonitorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.coordinator import HildebrandGlowEnergyMonitorDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HildebrandGlowDiagnosticSensorEntityDescription(SensorEntityDescription):
    """Entity description for diagnostic sensors."""


ENTITY_DESCRIPTIONS: tuple[HildebrandGlowDiagnosticSensorEntityDescription, ...] = (
    HildebrandGlowDiagnosticSensorEntityDescription(
        key="last_updated",
        translation_key="last_updated",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class HildebrandGlowDiagnosticSensor(SensorEntity, HildebrandGlowEnergyMonitorEntity):
    """Diagnostic sensor class for integration status."""

    entity_description: HildebrandGlowDiagnosticSensorEntityDescription

    def __init__(
        self,
        coordinator: HildebrandGlowEnergyMonitorDataUpdateCoordinator,
        entity_description: HildebrandGlowDiagnosticSensorEntityDescription,
        meter_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """
        Initialize the diagnostic sensor.

        Args:
            coordinator: The data update coordinator.
            entity_description: The entity description.
            meter_id: The virtual entity (meter) ID.
            device_info: The device info for this meter.

        """
        super().__init__(coordinator, entity_description)
        self._meter_id = meter_id
        # Override unique_id to include meter_id for multi-meter support
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{meter_id}_{entity_description.key}"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the last successful update."""
        return self.coordinator.last_update_success_time
