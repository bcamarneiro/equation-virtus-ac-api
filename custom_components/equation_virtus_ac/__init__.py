"""Equation Virtus AC integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EquationVirtusACApi
from .const import CONF_HOME_ID, CONF_NODE_ID, DOMAIN
from .coordinator import EquationVirtusACCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

SERVICE_SCHEDULE = "schedule"
SERVICE_TIMER = "timer"


def _get_api_for_service_call(
    hass: HomeAssistant, call: ServiceCall
) -> EquationVirtusACApi | None:
    """Get the API instance for a service call targeting a specific entity."""
    entity_ids: list[str] = call.data.get("entity_id", [])  # type: ignore[assignment]
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    if not entity_ids:
        _LOGGER.error("No entity targeted in service call")
        return None

    # Look up the config entry for the first targeted entity
    registry = hass.helpers.entity_registry.async_get(hass)
    for entity_id in entity_ids:
        entry = registry.async_get(entity_id)
        if entry and entry.config_entry_id:
            coordinator = hass.data.get(DOMAIN, {}).get(entry.config_entry_id)
            if isinstance(coordinator, EquationVirtusACCoordinator):
                return coordinator.api

    _LOGGER.error("No coordinator found for targeted entities: %s", entity_ids)
    return None


async def async_handle_schedule(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle the enki.schedule service call."""
    api = _get_api_for_service_call(hass, call)
    if api is None:
        return

    time: str = call.data["time"]
    days: list[str] = call.data["days"]
    power: str | None = call.data.get("power")
    target_temperature: float | None = call.data.get("target_temperature")
    operating_mode: str | None = call.data.get("operating_mode")

    success = await api.set_schedule(
        time=time,
        days=days,
        power=power,
        target_temperature=target_temperature,
        operating_mode=operating_mode,
    )

    if success:
        _LOGGER.info(
            "Schedule set: %s on %s — power=%s, temp=%s, mode=%s",
            time,
            ", ".join(days),
            power,
            target_temperature,
            operating_mode,
        )
        hass.bus.async_fire(
            "equation_virtus_ac_schedule_set",
            {
                "time": time,
                "days": days,
                "power": power,
                "target_temperature": target_temperature,
                "operating_mode": operating_mode,
            },
        )
    else:
        _LOGGER.error("Failed to set schedule")


async def async_handle_timer(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle the enki.timer service call."""
    api = _get_api_for_service_call(hass, call)
    if api is None:
        return

    duration: int = call.data["duration"]
    action: str = call.data["action"]
    target_temperature: float | None = call.data.get("target_temperature")
    operating_mode: str | None = call.data.get("operating_mode")

    success = await api.set_timer(
        duration=duration,
        action=action,
        target_temperature=target_temperature,
        operating_mode=operating_mode,
    )

    if success:
        _LOGGER.info(
            "Timer set: %d min, action=%s, temp=%s, mode=%s",
            duration,
            action,
            target_temperature,
            operating_mode,
        )
        hass.bus.async_fire(
            "equation_virtus_ac_timer_set",
            {
                "duration": duration,
                "action": action,
                "target_temperature": target_temperature,
                "operating_mode": operating_mode,
            },
        )
    else:
        _LOGGER.error("Failed to set timer")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Equation Virtus AC from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    api = EquationVirtusACApi(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        home_id=entry.data[CONF_HOME_ID],
        node_id=entry.data[CONF_NODE_ID],
    )

    # Authenticate
    if not await api.authenticate():
        _LOGGER.error("Failed to authenticate with Equation API")
        return False

    coordinator = EquationVirtusACCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register scheduling services
    hass.services.async_register(DOMAIN, SERVICE_SCHEDULE, async_handle_schedule)
    hass.services.async_register(DOMAIN, SERVICE_TIMER, async_handle_timer)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Remove services if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SCHEDULE)
            hass.services.async_remove(DOMAIN, SERVICE_TIMER)

    return unload_ok
