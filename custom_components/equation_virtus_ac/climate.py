"""Climate platform for Equation Virtus AC integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN,
    HVAC_MODE_HEAT,
    MAX_TEMP,
    MIN_TEMP,
    POWER_OFF,
    POWER_ON,
)
from .coordinator import EquationVirtusACCoordinator

_LOGGER = logging.getLogger(__name__)

# Map API modes to HA HVAC modes
HVAC_MODE_MAP = {
    HVAC_MODE_COOL: HVACMode.COOL,
    HVAC_MODE_HEAT: HVACMode.HEAT,
    HVAC_MODE_DRY: HVACMode.DRY,
    HVAC_MODE_FAN: HVACMode.FAN_ONLY,
    HVAC_MODE_AUTO: HVACMode.AUTO,
}

HVAC_MODE_REVERSE_MAP = {v: k for k, v in HVAC_MODE_MAP.items()}

# Map API fan speeds to HA fan modes
FAN_MODE_MAP = {
    FAN_LOW: "low",
    FAN_MEDIUM: "medium",
    FAN_HIGH: "high",
    FAN_AUTO: "auto",
}

FAN_MODE_REVERSE_MAP = {v: k for k, v in FAN_MODE_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    coordinator: EquationVirtusACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EquationVirtusACClimate(coordinator, entry)])


class EquationVirtusACClimate(CoordinatorEntity[EquationVirtusACCoordinator], ClimateEntity):
    """Climate entity for Equation Virtus AC."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1.0
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.AUTO,
    ]
    _attr_fan_modes = ["low", "medium", "high", "auto"]
    _attr_swing_modes = ["off", "vertical", "horizontal", "both"]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _enable_turn_on_off_backwards_compatibility = False

    # Optimistic state tracking
    _optimistic_state: dict[str, Any] | None = None

    def __init__(
        self,
        coordinator: EquationVirtusACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.data["node_id"]
        self._attr_device_info = coordinator.device_info
        self._optimistic_state = {}

    def _clear_optimistic(self) -> None:
        """Clear optimistic state after coordinator update."""
        self._optimistic_state = {}

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.coordinator.data:
            return self.coordinator.data.current_temperature
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if "target_temperature" in self._optimistic_state:
            return self._optimistic_state["target_temperature"]
        if self.coordinator.data:
            return self.coordinator.data.target_temperature
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if "hvac_mode" in self._optimistic_state:
            return self._optimistic_state["hvac_mode"]

        if not self.coordinator.data:
            return HVACMode.OFF

        if self.coordinator.data.power == POWER_OFF:
            return HVACMode.OFF

        api_mode = self.coordinator.data.operating_mode
        return HVAC_MODE_MAP.get(api_mode, HVACMode.AUTO)

    @property
    def fan_mode(self) -> str | None:
        """Return the fan mode."""
        if "fan_mode" in self._optimistic_state:
            return self._optimistic_state["fan_mode"]
        if self.coordinator.data:
            api_fan = self.coordinator.data.fan_speed
            return FAN_MODE_MAP.get(api_fan, "auto")
        return None

    @property
    def swing_mode(self) -> str | None:
        """Return the swing mode."""
        if "swing_mode" in self._optimistic_state:
            return self._optimistic_state["swing_mode"]

        if not self.coordinator.data:
            return None

        swing = self.coordinator.data.swing_orientation
        h_auto = swing.horizontal == "AUTO"
        v_auto = swing.vertical == "AUTO"

        if h_auto and v_auto:
            return "both"
        elif v_auto:
            return "vertical"
        elif h_auto:
            return "horizontal"
        return "off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        return {
            "health_mode": self.coordinator.data.health_mode,
            "frost_protection_mode": self.coordinator.data.frost_protection_mode,
            "self_clean_mode": self.coordinator.data.self_clean_mode,
            "quiet_mode": self.coordinator.data.quiet_mode,
            "sleep_mode": self.coordinator.data.sleep_mode,
            "defrost_mode": self.coordinator.data.defrost_mode,
            "last_reported": self.coordinator.data.last_reported_date,
        }

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        # Set optimistic state immediately
        self._optimistic_state["hvac_mode"] = hvac_mode
        self.async_write_ha_state()

        if hvac_mode == HVACMode.OFF:
            await self.coordinator.api.set_state(power=POWER_OFF)
        else:
            api_mode = HVAC_MODE_REVERSE_MAP.get(hvac_mode)
            if api_mode:
                await self.coordinator.api.set_state(
                    power=POWER_ON,
                    operating_mode=api_mode,
                )

        await self.coordinator.async_request_refresh()
        self._clear_optimistic()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            # Set optimistic state immediately
            self._optimistic_state["target_temperature"] = temperature
            self.async_write_ha_state()

            await self.coordinator.api.set_state(target_temperature=temperature)
            await self.coordinator.async_request_refresh()
            self._clear_optimistic()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        # Set optimistic state immediately
        self._optimistic_state["fan_mode"] = fan_mode
        self.async_write_ha_state()

        api_fan = FAN_MODE_REVERSE_MAP.get(fan_mode)
        if api_fan:
            await self.coordinator.api.set_state(fan_speed=api_fan)
            await self.coordinator.async_request_refresh()
            self._clear_optimistic()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set swing mode."""
        # Set optimistic state immediately
        self._optimistic_state["swing_mode"] = swing_mode
        self.async_write_ha_state()

        if swing_mode == "off":
            h_mode = "NIV_1"
            v_mode = "NIV_1"
        elif swing_mode == "vertical":
            h_mode = None
            v_mode = "AUTO"
        elif swing_mode == "horizontal":
            h_mode = "AUTO"
            v_mode = None
        else:  # both
            h_mode = "AUTO"
            v_mode = "AUTO"

        await self.coordinator.api.set_state(
            swing_horizontal=h_mode,
            swing_vertical=v_mode,
        )
        await self.coordinator.async_request_refresh()
        self._clear_optimistic()

    async def async_turn_on(self) -> None:
        """Turn on the AC."""
        # Set optimistic state - use last known mode or AUTO
        last_mode = HVACMode.AUTO
        if self.coordinator.data and self.coordinator.data.operating_mode:
            last_mode = HVAC_MODE_MAP.get(self.coordinator.data.operating_mode, HVACMode.AUTO)
        self._optimistic_state["hvac_mode"] = last_mode
        self.async_write_ha_state()

        await self.coordinator.api.set_state(power=POWER_ON)
        await self.coordinator.async_request_refresh()
        self._clear_optimistic()

    async def async_turn_off(self) -> None:
        """Turn off the AC."""
        # Set optimistic state immediately
        self._optimistic_state["hvac_mode"] = HVACMode.OFF
        self.async_write_ha_state()

        await self.coordinator.api.set_state(power=POWER_OFF)
        await self.coordinator.async_request_refresh()
        self._clear_optimistic()
