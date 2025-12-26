"""Switch platform for Equation Virtus AC integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ACState
from .const import DOMAIN
from .coordinator import EquationVirtusACCoordinator


@dataclass(frozen=True, kw_only=True)
class EquationSwitchEntityDescription(SwitchEntityDescription):
    """Describes Equation Virtus AC switch entity."""

    value_fn: Callable[[ACState], bool]
    api_field: str


SWITCH_DESCRIPTIONS: tuple[EquationSwitchEntityDescription, ...] = (
    EquationSwitchEntityDescription(
        key="quiet_mode",
        translation_key="quiet_mode",
        name="Quiet Mode",
        icon="mdi:volume-off",
        value_fn=lambda state: state.quiet_mode,
        api_field="quiet_mode",
    ),
    EquationSwitchEntityDescription(
        key="sleep_mode",
        translation_key="sleep_mode",
        name="Sleep Mode",
        icon="mdi:sleep",
        value_fn=lambda state: state.sleep_mode,
        api_field="sleep_mode",
    ),
    EquationSwitchEntityDescription(
        key="health_mode",
        translation_key="health_mode",
        name="Health Mode",
        icon="mdi:air-filter",
        value_fn=lambda state: state.health_mode,
        api_field="health_mode",
    ),
    EquationSwitchEntityDescription(
        key="frost_protection_mode",
        translation_key="frost_protection_mode",
        name="Frost Protection",
        icon="mdi:snowflake-alert",
        value_fn=lambda state: state.frost_protection_mode,
        api_field="frost_protection_mode",
    ),
    EquationSwitchEntityDescription(
        key="self_clean_mode",
        translation_key="self_clean_mode",
        name="Self Clean",
        icon="mdi:vacuum",
        value_fn=lambda state: state.self_clean_mode,
        api_field="self_clean_mode",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator: EquationVirtusACCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EquationVirtusACSwitch(coordinator, entry, description)
        for description in SWITCH_DESCRIPTIONS
    )


class EquationVirtusACSwitch(CoordinatorEntity[EquationVirtusACCoordinator], SwitchEntity):
    """Switch entity for Equation Virtus AC special modes."""

    entity_description: EquationSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
        description: EquationSwitchEntityDescription,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.data['node_id']}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._set_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._set_mode(False)

    async def _set_mode(self, value: bool) -> None:
        """Set the mode value."""
        api_field = self.entity_description.api_field
        await self.coordinator.api.set_state(**{api_field: value})
        await self.coordinator.async_request_refresh()
