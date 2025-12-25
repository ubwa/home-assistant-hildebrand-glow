"""Gas consumption sensors for hildebrand_glow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from custom_components.hildebrand_glow.entity import HildebrandGlowEnergyMonitorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.coordinator import HildebrandGlowEnergyMonitorDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HildebrandGlowGasSensorEntityDescription(SensorEntityDescription):
    """Entity description for gas sensors."""

    data_key: str


ENTITY_DESCRIPTIONS: tuple[HildebrandGlowGasSensorEntityDescription, ...] = (
    # Usage sensors (enabled by default)
    HildebrandGlowGasSensorEntityDescription(
        key="gas_usage_today",
        translation_key="gas_usage_today",
        icon="mdi:fire",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        data_key="gas_usage_today",
    ),
    HildebrandGlowGasSensorEntityDescription(
        key="gas_usage_week",
        translation_key="gas_usage_week",
        icon="mdi:fire",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        data_key="gas_usage_week",
    ),
    HildebrandGlowGasSensorEntityDescription(
        key="gas_usage_month",
        translation_key="gas_usage_month",
        icon="mdi:fire",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        data_key="gas_usage_month",
    ),
    # Cost sensors (enabled by default)
    HildebrandGlowGasSensorEntityDescription(
        key="gas_cost_today",
        translation_key="gas_cost_today",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        data_key="gas_cost_today",
    ),
    HildebrandGlowGasSensorEntityDescription(
        key="gas_cost_week",
        translation_key="gas_cost_week",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        data_key="gas_cost_week",
    ),
    HildebrandGlowGasSensorEntityDescription(
        key="gas_cost_month",
        translation_key="gas_cost_month",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        data_key="gas_cost_month",
    ),
)


class HildebrandGlowGasSensor(SensorEntity, HildebrandGlowEnergyMonitorEntity):
    """Gas consumption sensor class."""

    entity_description: HildebrandGlowGasSensorEntityDescription

    def __init__(
        self,
        coordinator: HildebrandGlowEnergyMonitorDataUpdateCoordinator,
        entity_description: HildebrandGlowGasSensorEntityDescription,
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
        return self._meter_data.get("has_gas", False)

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self._meter_data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "meter_id": self._meter_id,
            "postal_code": self._meter_data.get("postal_code"),
        }
