"""Sensor platform for Equation Virtus AC integration."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EquationVirtusACCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: EquationVirtusACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EquationVirtusACLastReportedSensor(coordinator, entry)])


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
