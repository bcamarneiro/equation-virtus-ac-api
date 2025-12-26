"""Select platform for Equation Virtus AC integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EquationVirtusACCoordinator

_LOGGER = logging.getLogger(__name__)

# Swing position options
VERTICAL_OPTIONS = ["auto", "position_1", "position_2", "position_3", "position_4"]
HORIZONTAL_OPTIONS = ["auto", "position_1", "position_2", "position_3", "position_4", "position_5"]

# Map display names to API values
SWING_TO_API = {
    "auto": "AUTO",
    "position_1": "NIV_1",
    "position_2": "NIV_2",
    "position_3": "NIV_3",
    "position_4": "NIV_4",
    "position_5": "NIV_5",
}

API_TO_SWING = {v: k for k, v in SWING_TO_API.items()}


@dataclass(frozen=True, kw_only=True)
class EquationSelectEntityDescription(SelectEntityDescription):
    """Describes Equation select entity."""

    options_list: list[str]
    is_horizontal: bool


SELECT_DESCRIPTIONS: tuple[EquationSelectEntityDescription, ...] = (
    EquationSelectEntityDescription(
        key="vertical_swing",
        name="Vertical Swing",
        icon="mdi:arrow-up-down",
        options_list=VERTICAL_OPTIONS,
        is_horizontal=False,
    ),
    EquationSelectEntityDescription(
        key="horizontal_swing",
        name="Horizontal Swing",
        icon="mdi:arrow-left-right",
        options_list=HORIZONTAL_OPTIONS,
        is_horizontal=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator: EquationVirtusACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EquationVirtusACSelect(coordinator, entry, description)
        for description in SELECT_DESCRIPTIONS
    )


class EquationVirtusACSelect(CoordinatorEntity[EquationVirtusACCoordinator], SelectEntity):
    """Select entity for Equation Virtus AC swing control."""

    entity_description: EquationSelectEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
        description: EquationSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data['node_id']}_{description.key}"
        self._attr_device_info = coordinator.device_info
        self._attr_options = description.options_list
        self._optimistic_value: str | None = None

    @property
    def current_option(self) -> str | None:
        """Return the current swing position."""
        if self._optimistic_value is not None:
            return self._optimistic_value

        if not self.coordinator.data:
            return None

        swing = self.coordinator.data.swing_orientation
        if self.entity_description.is_horizontal:
            api_value = swing.horizontal
        else:
            api_value = swing.vertical

        return API_TO_SWING.get(api_value, "auto")

    async def async_select_option(self, option: str) -> None:
        """Set the swing position."""
        # Set optimistic state immediately
        self._optimistic_value = option
        self.async_write_ha_state()

        api_value = SWING_TO_API.get(option, "AUTO")

        if self.entity_description.is_horizontal:
            await self.coordinator.api.set_state(swing_horizontal=api_value)
        else:
            await self.coordinator.api.set_state(swing_vertical=api_value)

        await self.coordinator.async_request_refresh()
        self._optimistic_value = None
