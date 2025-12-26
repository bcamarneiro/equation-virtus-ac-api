"""API client for Equation Virtus AC."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from .const import (
    API_KEY_AIRCO,
    API_KEY_NODE,
    BASE_URL,
    CLIENT_ID,
    ENDPOINT_CHANGE_STATE,
    ENDPOINT_CHECK_ERROR,
    ENDPOINT_CHECK_STATE,
    ENDPOINT_DASHBOARD,
    ENDPOINT_NODE_INFO,
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class SwingOrientation:
    """Swing orientation settings."""

    horizontal: str
    vertical: str


@dataclass
class ACState:
    """Current state of the AC."""

    target_temperature: float
    current_temperature: float
    operating_mode: str
    power: str
    fan_speed: str
    swing_orientation: SwingOrientation
    health_mode: bool
    frost_protection_mode: bool
    self_clean_mode: bool
    quiet_mode: bool
    sleep_mode: bool
    defrost_mode: bool
    last_reported_date: str


@dataclass
class DeviceInfo:
    """Device information."""

    node_id: str
    device_id: str
    home_id: str
    label: str
    model_number: str
    factory_id: str
    icon: str


class EquationVirtusACApi:
    """API client for Equation Virtus AC."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        home_id: str | None = None,
        node_id: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._username = username
        self._password = password
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._home_id = home_id
        self._node_id = node_id
        self._token_expires: datetime | None = None

    @property
    def access_token(self) -> str | None:
        """Return the access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Return the refresh token."""
        return self._refresh_token

    @property
    def home_id(self) -> str | None:
        """Return the home ID."""
        return self._home_id

    @property
    def node_id(self) -> str | None:
        """Return the node ID."""
        return self._node_id

    async def authenticate(self) -> bool:
        """Authenticate with the API using username and password."""
        if not self._username or not self._password:
            return False

        data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": self._username,
            "password": self._password,
        }

        try:
            async with self._session.post(TOKEN_URL, data=data) as response:
                if response.status != 200:
                    _LOGGER.error("Authentication failed: %s", response.status)
                    return False

                result = await response.json()
                self._access_token = result["access_token"]
                self._refresh_token = result["refresh_token"]
                expires_in = result.get("expires_in", 7200)
                self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Authentication error: %s", err)
            return False

    async def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            return await self.authenticate()

        data = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": self._refresh_token,
        }

        try:
            async with self._session.post(TOKEN_URL, data=data) as response:
                if response.status != 200:
                    _LOGGER.warning("Token refresh failed, re-authenticating")
                    return await self.authenticate()

                result = await response.json()
                self._access_token = result["access_token"]
                self._refresh_token = result["refresh_token"]
                expires_in = result.get("expires_in", 7200)
                self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Token refresh error: %s", err)
            return False

    async def _ensure_token_valid(self) -> bool:
        """Ensure the access token is valid."""
        if not self._access_token:
            return await self.authenticate()

        if self._token_expires and datetime.now() >= self._token_expires:
            return await self.refresh_access_token()

        return True

    def _get_headers(self, api_key: str = API_KEY_AIRCO) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "x-gateway-apikey": api_key,
            "authorization": f"Bearer {self._access_token}",
            "content-type": "application/json; charset=utf-8",
            "user-agent": "EquationVirtusAC-HA/1.0",
        }
        if self._home_id:
            headers["homeid"] = self._home_id
        return headers

    async def get_state(self) -> ACState | None:
        """Get the current state of the AC."""
        if not await self._ensure_token_valid():
            return None

        if not self._node_id:
            _LOGGER.error("Node ID not set")
            return None

        url = BASE_URL + ENDPOINT_CHECK_STATE.format(node_id=self._node_id)

        try:
            async with self._session.get(url, headers=self._get_headers()) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to get state: %s", response.status)
                    return None

                data = await response.json()
                value = data["lastReportedValue"]

                return ACState(
                    target_temperature=value["targetTemperature"],
                    current_temperature=value["currentTemperature"],
                    operating_mode=value["operatingMode"],
                    power=value["power"],
                    fan_speed=value["fanSpeed"],
                    swing_orientation=SwingOrientation(
                        horizontal=value["swingOrientation"]["horizontal"],
                        vertical=value["swingOrientation"]["vertical"],
                    ),
                    health_mode=value["healthMode"],
                    frost_protection_mode=value["frostProtectionMode"],
                    self_clean_mode=value["selfCleanMode"],
                    quiet_mode=value["quietMode"],
                    sleep_mode=value["sleepMode"],
                    defrost_mode=value["defrostMode"],
                    last_reported_date=data["lastReportedDate"],
                )

        except (aiohttp.ClientError, KeyError) as err:
            _LOGGER.error("Error getting state: %s", err)
            return None

    async def set_state(
        self,
        *,
        power: str | None = None,
        target_temperature: float | None = None,
        operating_mode: str | None = None,
        fan_speed: str | None = None,
        health_mode: bool | None = None,
        frost_protection_mode: bool | None = None,
        self_clean_mode: bool | None = None,
        quiet_mode: bool | None = None,
        sleep_mode: bool | None = None,
        swing_horizontal: str | None = None,
        swing_vertical: str | None = None,
    ) -> bool:
        """Set the state of the AC."""
        if not await self._ensure_token_valid():
            return False

        if not self._node_id:
            _LOGGER.error("Node ID not set")
            return False

        url = BASE_URL + ENDPOINT_CHANGE_STATE.format(node_id=self._node_id)

        swing_orientation = None
        if swing_horizontal is not None or swing_vertical is not None:
            swing_orientation = {
                "horizontal": swing_horizontal or "AUTO",
                "vertical": swing_vertical or "AUTO",
            }

        payload = {
            "targetTemperature": target_temperature,
            "currentTemperature": None,
            "operatingMode": operating_mode,
            "power": power,
            "fanSpeed": fan_speed,
            "frostProtectionMode": frost_protection_mode if frost_protection_mode is not None else False,
            "selfCleanMode": self_clean_mode if self_clean_mode is not None else False,
            "healthMode": health_mode if health_mode is not None else False,
            "quietMode": quiet_mode if quiet_mode is not None else False,
            "sleepMode": sleep_mode if sleep_mode is not None else False,
            "swingOrientation": swing_orientation,
        }

        try:
            async with self._session.post(url, headers=self._get_headers(), json=payload) as response:
                if response.status == 202:
                    return True
                _LOGGER.error("Failed to set state: %s", response.status)
                return False

        except aiohttp.ClientError as err:
            _LOGGER.error("Error setting state: %s", err)
            return False

    async def get_error(self) -> dict[str, Any] | None:
        """Get any error codes from the AC."""
        if not await self._ensure_token_valid():
            return None

        if not self._node_id:
            return None

        url = BASE_URL + ENDPOINT_CHECK_ERROR.format(node_id=self._node_id)

        try:
            async with self._session.get(url, headers=self._get_headers()) as response:
                if response.status != 200:
                    return None
                return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error getting error state: %s", err)
            return None

    async def get_device_info(self) -> DeviceInfo | None:
        """Get device information."""
        if not await self._ensure_token_valid():
            return None

        if not self._node_id:
            return None

        url = BASE_URL + ENDPOINT_NODE_INFO.format(node_id=self._node_id)

        try:
            async with self._session.get(url, headers=self._get_headers(API_KEY_NODE)) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                return DeviceInfo(
                    node_id=data["id"],
                    device_id=data["deviceId"],
                    home_id=data["homeId"],
                    label=data["label"],
                    model_number=data["modelNumber"],
                    factory_id=data["factoryId"],
                    icon=data["icon"],
                )

        except (aiohttp.ClientError, KeyError) as err:
            _LOGGER.error("Error getting device info: %s", err)
            return None

    async def discover_devices(self) -> list[dict[str, Any]]:
        """Discover AC devices in the home."""
        if not await self._ensure_token_valid():
            return []

        if not self._home_id:
            _LOGGER.error("Home ID not set")
            return []

        url = BASE_URL + ENDPOINT_DASHBOARD.format(home_id=self._home_id) + "?hasGroups=true"

        try:
            async with self._session.get(url, headers=self._get_headers(API_KEY_NODE)) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                devices = []

                # Look for air conditioner nodes
                for node in data.get("nodes", []):
                    if node.get("icon") == "air_conditioners":
                        devices.append({
                            "node_id": node["id"],
                            "label": node.get("label", "AC"),
                            "icon": node.get("icon"),
                        })

                return devices

        except (aiohttp.ClientError, KeyError) as err:
            _LOGGER.error("Error discovering devices: %s", err)
            return []
