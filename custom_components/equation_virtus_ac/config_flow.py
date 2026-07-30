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
    CONF_TIMER_DEFAULT_DURATION,
    DEFAULT_TIMER_DURATION,
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
        self._devices: list[dict[str, Any]] = []
        self._pending_node_id: str | None = None
        self._pending_device_name: str | None = None
        self._timer_duration: int = DEFAULT_TIMER_DURATION

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

    async def async_step_home(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle home ID input."""
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
                "info": "Enter your Home ID from the Enki app. You can find this in the app settings or by inspecting network traffic.",
            },
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection."""
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

            self._pending_node_id = node_id
            self._pending_device_name = device_name

            return await self.async_step_timer()

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
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual configuration."""
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
                self._pending_node_id = node_id
                self._pending_device_name = device_info.label

                return await self.async_step_timer()
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
        )

    async def async_step_timer(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle timer default configuration."""
        if user_input is not None:
            self._timer_duration = user_input.get(
                CONF_TIMER_DEFAULT_DURATION, DEFAULT_TIMER_DURATION
            )

            return self.async_create_entry(
                title=self._pending_device_name,
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_HOME_ID: self._home_id,
                    CONF_NODE_ID: self._pending_node_id,
                    CONF_DEVICE_NAME: self._pending_device_name,
                    CONF_TIMER_DEFAULT_DURATION: self._timer_duration,
                },
            )

        return self.async_show_form(
            step_id="timer",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TIMER_DEFAULT_DURATION,
                        default=DEFAULT_TIMER_DURATION,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                }
            ),
            description_placeholders={
                "info": "Set the default timer duration in minutes. You can override this when calling the enki.timer service.",
            },
        )
