"""Config flow for Equation Virtus AC integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EquationVirtusACApi
from .const import (
    CONF_HOME_ID,
    CONF_NODE_ID,
    CONF_DEVICE_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class EquationVirtusACConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Equation Virtus AC."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api: EquationVirtusACApi | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._home_id: str | None = None
        self._homes: list[dict[str, Any]] = []
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - user credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            self._api = EquationVirtusACApi(
                session=session,
                username=self._username,
                password=self._password,
            )

            if await self._api.authenticate():
                # Auto-discover homes for the authenticated user
                _LOGGER.debug("Authentication successful, discovering homes")
                self._homes = await self._api.discover_homes()

                if self._homes:
                    _LOGGER.debug(
                        "Auto-discovered %d home(s), showing selection",
                        len(self._homes),
                    )
                    return await self.async_step_home_select()
                else:
                    # Legacy fallback: manual Home ID entry
                    _LOGGER.warning(
                        "No homes discovered via API, falling back to manual entry"
                    )
                    return await self.async_step_home()
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "app_name": "Enki",
            },
        )

    async def async_step_home_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle home selection from auto-discovered homes."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._home_id = user_input[CONF_HOME_ID]
            self._api._home_id = self._home_id

            # Auto-discover devices in the selected home
            self._devices = await self._api.discover_devices()
            _LOGGER.debug(
                "Discovered %d device(s) for home %s",
                len(self._devices),
                self._home_id,
            )

            if self._devices:
                return await self.async_step_device()
            else:
                # No devices found, offer manual node entry
                _LOGGER.warning(
                    "No devices discovered in home %s, proceeding to manual entry",
                    self._home_id,
                )
                return await self.async_step_manual()

        # Build home selection options
        home_options = {
            home["home_id"]: _format_home_label(home)
            for home in self._homes
        }

        return self.async_show_form(
            step_id="home_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOME_ID): vol.In(home_options),
                }
            ),
            errors=errors,
            description_placeholders={
                "count": str(len(self._homes)),
            },
        )

    async def async_step_home(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual Home ID input (legacy fallback).

        Deprecated: auto-discovery via async_step_home_select is preferred.
        This step is kept for cases where the homes API is unavailable.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            self._home_id = user_input[CONF_HOME_ID]
            self._api._home_id = self._home_id

            # Discover devices
            self._devices = await self._api.discover_devices()
            _LOGGER.debug("Discovered devices: %s", self._devices)

            if self._devices:
                return await self.async_step_device()
            else:
                # No devices found, go to manual entry
                _LOGGER.warning("No devices discovered, proceeding to manual entry")
                return await self.async_step_manual()

        return self.async_show_form(
            step_id="home",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOME_ID): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "info": (
                    "Enter your Home ID from the Enki app. "
                    "You can find this in the app settings or by inspecting network traffic. "
                    "This is a legacy fallback — auto-discovery is preferred."
                ),
            },
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection from auto-discovered devices."""
        if user_input is not None:
            node_id = user_input[CONF_NODE_ID]

            # Find the selected device
            device = next(
                (d for d in self._devices if d["node_id"] == node_id), None
            )
            device_name = device["label"] if device else "AC"

            # Check if already configured
            await self.async_set_unique_id(node_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_HOME_ID: self._home_id,
                    CONF_NODE_ID: node_id,
                    CONF_DEVICE_NAME: device_name,
                },
            )

        # Build device selection options
        device_options = {
            device["node_id"]: f"{device['label']} ({device['node_id'][:8]}...)"
            for device in self._devices
        }

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NODE_ID): vol.In(device_options),
                }
            ),
            description_placeholders={
                "home_id": self._home_id or "unknown",
            },
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual Node ID entry (legacy fallback).

        Deprecated: auto-discovery via async_step_device is preferred.
        This step is kept for cases where device discovery fails.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            node_id = user_input[CONF_NODE_ID]

            # Check if already configured
            await self.async_set_unique_id(node_id)
            self._abort_if_unique_id_configured()

            self._api._node_id = node_id

            # Try to get device info to validate
            device_info = await self._api.get_device_info()
            if device_info:
                return self.async_create_entry(
                    title=device_info.label,
                    data={
                        CONF_USERNAME: self._username,
                        CONF_PASSWORD: self._password,
                        CONF_HOME_ID: self._home_id,
                        CONF_NODE_ID: node_id,
                        CONF_DEVICE_NAME: device_info.label,
                    },
                )
            else:
                errors["base"] = "invalid_device"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NODE_ID): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "info": (
                    "Enter the Node ID manually. "
                    "This is a legacy fallback — auto-discovery is preferred."
                ),
            },
        )


def _format_home_label(home: dict[str, Any]) -> str:
    """Format a home entry into a readable label for the selection dropdown."""
    name = home.get("name", "")
    address = home.get("address")

    if address:
        return f"{name} — {address}"
    return name or f"Home {home['home_id'][:8]}"
