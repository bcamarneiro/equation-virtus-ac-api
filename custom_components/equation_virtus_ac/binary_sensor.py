"""Binary sensor platform for Equation Virtus AC integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
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
    """Set up the binary sensor platform."""
    coordinator: EquationVirtusACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EquationVirtusACDefrostSensor(coordinator, entry)])


class EquationVirtusACDefrostSensor(CoordinatorEntity[EquationVirtusACCoordinator], BinarySensorEntity):
    """Binary sensor for defrost mode status."""

    _attr_has_entity_name = True
    _attr_name = "Defrost"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:snowflake-melt"

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['node_id']}_defrost"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if defrost is active."""
        if self.coordinator.data:
            return self.coordinator.data.defrost_mode
        return None
