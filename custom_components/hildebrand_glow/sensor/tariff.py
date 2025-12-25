"""Tariff sensors for hildebrand_glow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from custom_components.hildebrand_glow.entity import HildebrandGlowEnergyMonitorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.coordinator import HildebrandGlowEnergyMonitorDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HildebrandGlowTariffSensorEntityDescription(SensorEntityDescription):
    """Entity description for tariff sensors."""

    data_key: str
    energy_type: str  # "electricity" or "gas"


ENTITY_DESCRIPTIONS: tuple[HildebrandGlowTariffSensorEntityDescription, ...] = (
    # Electricity tariff sensors (disabled by default)
    HildebrandGlowTariffSensorEntityDescription(
        key="electricity_rate",
        translation_key="electricity_rate",
        icon="mdi:currency-gbp",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="p/kWh",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        data_key="electricity_rate",
        energy_type="electricity",
    ),
    HildebrandGlowTariffSensorEntityDescription(
        key="electricity_standing_charge",
        translation_key="electricity_standing_charge",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        data_key="electricity_standing_charge",
        energy_type="electricity",
    ),
    # Gas tariff sensors (disabled by default)
    HildebrandGlowTariffSensorEntityDescription(
        key="gas_rate",
        translation_key="gas_rate",
        icon="mdi:currency-gbp",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="p/kWh",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        data_key="gas_rate",
        energy_type="gas",
    ),
    HildebrandGlowTariffSensorEntityDescription(
        key="gas_standing_charge",
        translation_key="gas_standing_charge",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        data_key="gas_standing_charge",
        energy_type="gas",
    ),
)


class HildebrandGlowTariffSensor(SensorEntity, HildebrandGlowEnergyMonitorEntity):
    """Tariff sensor class."""

    entity_description: HildebrandGlowTariffSensorEntityDescription

    def __init__(
        self,
        coordinator: HildebrandGlowEnergyMonitorDataUpdateCoordinator,
        entity_description: HildebrandGlowTariffSensorEntityDescription,
        meter_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """
        Initialize the sensor.

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
    def _meter_data(self) -> dict[str, Any]:
        """Get the meter data from coordinator."""
        meters = self.coordinator.data.get("meters", {})
        return meters.get(self._meter_id, {})

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        # Check if the relevant energy type is available
        energy_type = self.entity_description.energy_type
        return self._meter_data.get(f"has_{energy_type}", False)

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self._meter_data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "meter_id": self._meter_id,
        }
