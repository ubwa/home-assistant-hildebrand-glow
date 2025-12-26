"""Electricity consumption sensors for hildebrand_glow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from custom_components.hildebrand_glow.entity import HildebrandGlowEnergyMonitorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from custom_components.hildebrand_glow.coordinator import HildebrandGlowEnergyMonitorDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HildebrandGlowElectricitySensorEntityDescription(SensorEntityDescription):
    """Entity description for electricity sensors."""

    data_key: str


ENTITY_DESCRIPTIONS: tuple[HildebrandGlowElectricitySensorEntityDescription, ...] = (
    # Real-time power sensor (enabled by default)
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_power_current",
        translation_key="electricity_power_current",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        suggested_display_precision=3,
        data_key="electricity_power_current",
    ),
    # Usage sensors (enabled by default)
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_usage_today",
        translation_key="electricity_usage_today",
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        data_key="electricity_usage_today",
    ),
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_usage_week",
        translation_key="electricity_usage_week",
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        data_key="electricity_usage_week",
    ),
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_usage_month",
        translation_key="electricity_usage_month",
        icon="mdi:lightning-bolt",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        data_key="electricity_usage_month",
    ),
    # Cost sensors (enabled by default)
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_cost_today",
        translation_key="electricity_cost_today",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        data_key="electricity_cost_today",
    ),
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_cost_week",
        translation_key="electricity_cost_week",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        data_key="electricity_cost_week",
    ),
    HildebrandGlowElectricitySensorEntityDescription(
        key="electricity_cost_month",
        translation_key="electricity_cost_month",
        icon="mdi:currency-gbp",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="GBP",
        suggested_display_precision=2,
        data_key="electricity_cost_month",
    ),
)


class HildebrandGlowElectricitySensor(SensorEntity, HildebrandGlowEnergyMonitorEntity):
    """Electricity consumption sensor class."""

    entity_description: HildebrandGlowElectricitySensorEntityDescription

    def __init__(
        self,
        coordinator: HildebrandGlowEnergyMonitorDataUpdateCoordinator,
        entity_description: HildebrandGlowElectricitySensorEntityDescription,
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
        return self._meter_data.get("has_electricity", False)

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
