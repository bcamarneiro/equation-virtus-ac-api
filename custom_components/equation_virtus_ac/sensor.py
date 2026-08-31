"""Sensor platform for Equation Virtus AC integration."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import EnergyData
from .const import DOMAIN
from .coordinator import EquationVirtusACCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: EquationVirtusACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        EquationVirtusACLastReportedSensor(coordinator, entry),
        EquationVirtusACPowerSensor(coordinator, entry),
        EquationVirtusACDailyEnergySensor(coordinator, entry),
        EquationVirtusACMonthlyEnergySensor(coordinator, entry),
    ])


class EquationVirtusACLastReportedSensor(CoordinatorEntity[EquationVirtusACCoordinator], SensorEntity):
    """Sensor for last reported timestamp."""

    _attr_has_entity_name = True
    _attr_name = "Last Reported"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['node_id']}_last_reported"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> datetime | None:
        """Return the last reported timestamp."""
        if self.coordinator.data and self.coordinator.data.last_reported_date:
            try:
                return datetime.fromisoformat(
                    self.coordinator.data.last_reported_date.replace("Z", "+00:00")
                )
            except ValueError:
                return None
        return None


class EquationVirtusACPowerSensor(CoordinatorEntity[EquationVirtusACCoordinator], SensorEntity):
    """Sensor for current power consumption."""

    _attr_has_entity_name = True
    _attr_name = "Current Power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:flash"

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['node_id']}_current_power"
        self._attr_device_info = coordinator.device_info
        self._energy_data: EnergyData | None = None

    async def async_update(self) -> None:
        """Fetch energy data from the API."""
        self._energy_data = await self.coordinator.api.get_energy_current()

    @property
    def native_value(self) -> float | None:
        """Return the current power consumption."""
        if self._energy_data:
            return self._energy_data.current_power
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._energy_data is not None


class EquationVirtusACDailyEnergySensor(CoordinatorEntity[EquationVirtusACCoordinator], SensorEntity):
    """Sensor for daily energy consumption."""

    _attr_has_entity_name = True
    _attr_name = "Daily Energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:chart-bell-curve"

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['node_id']}_daily_energy"
        self._attr_device_info = coordinator.device_info
        self._energy_data: EnergyData | None = None

    async def async_update(self) -> None:
        """Fetch energy data from the API."""
        self._energy_data = await self.coordinator.api.get_energy_consumption()

    @property
    def native_value(self) -> float | None:
        """Return the daily energy consumption."""
        if self._energy_data:
            return self._energy_data.daily_consumption
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._energy_data is not None


class EquationVirtusACMonthlyEnergySensor(CoordinatorEntity[EquationVirtusACCoordinator], SensorEntity):
    """Sensor for monthly energy consumption."""

    _attr_has_entity_name = True
    _attr_name = "Monthly Energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:chart-bar"

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['node_id']}_monthly_energy"
        self._attr_device_info = coordinator.device_info
        self._energy_data: EnergyData | None = None

    async def async_update(self) -> None:
        """Fetch energy data from the API."""
        self._energy_data = await self.coordinator.api.get_energy_consumption()

    @property
    def native_value(self) -> float | None:
        """Return the monthly energy consumption."""
        if self._energy_data:
            return self._energy_data.monthly_consumption
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._energy_data is not None
