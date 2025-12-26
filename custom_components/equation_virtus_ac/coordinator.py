"""Data update coordinator for Equation Virtus AC."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ACState, EquationVirtusACApi
from .const import CONF_DEVICE_NAME, CONF_NODE_ID, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EquationVirtusACCoordinator(DataUpdateCoordinator[ACState | None]):
    """Coordinator for Equation Virtus AC data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: EquationVirtusACApi,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Equation Virtus AC ({entry.data.get(CONF_DEVICE_NAME, 'AC')})",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api = api
        self._entry = entry
        self._device_info: DeviceInfo | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        node_id = self._entry.data[CONF_NODE_ID]
        device_name = self._entry.data.get(CONF_DEVICE_NAME, "AC")

        return DeviceInfo(
            identifiers={(DOMAIN, node_id)},
            name=device_name,
            manufacturer="Equation",
            model="Virtus AC (AD-WMACKC-U1)",
            sw_version="1.0",
        )

    async def _async_update_data(self) -> ACState | None:
        """Fetch data from API."""
        try:
            state = await self.api.get_state()
            if state is None:
                raise UpdateFailed("Failed to fetch AC state")
            return state
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
