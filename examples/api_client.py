"""
Example API client for Equation Virtus AC.

This is a simple example showing how to interact with the API.
For production use, consider proper error handling and token refresh.
"""

import requests
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class OperatingMode(Enum):
    COOL = "COOL"
    HEAT = "HEAT"
    FAN = "FAN"
    DRY = "DRY"
    AUTO = "AUTO"


class FanSpeed(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    AUTO = "AUTO"


class Power(Enum):
    ON = "ON"
    OFF = "OFF"


@dataclass
class SwingOrientation:
    horizontal: str = "AUTO"
    vertical: str = "AUTO"


@dataclass
class ACState:
    target_temperature: float
    current_temperature: float
    operating_mode: OperatingMode
    power: Power
    fan_speed: FanSpeed
    swing_orientation: SwingOrientation
    health_mode: bool
    frost_protection_mode: bool
    self_clean_mode: bool
    quiet_mode: bool
    sleep_mode: bool
    defrost_mode: bool
    last_reported_date: str


class EquationVirtusAC:
    """Client for Equation Virtus AC API."""

    BASE_URL = "https://enki.api.devportal.adeo.cloud"
    API_KEY = "Nntj37xS5lih1qqFy8SbyHWKG5NEhSCm"

    def __init__(self, access_token: str, home_id: str, node_id: str):
        """Initialize the client.

        Args:
            access_token: JWT access token from Keycloak
            home_id: Home ID from the Enki app
            node_id: Node ID (device) from the Enki app
        """
        self.access_token = access_token
        self.home_id = home_id
        self.node_id = node_id
        self.session = requests.Session()
        self.session.headers.update({
            "x-gateway-apikey": self.API_KEY,
            "authorization": f"Bearer {access_token}",
            "homeid": home_id,
            "content-type": "application/json; charset=utf-8",
            "user-agent": "EquationVirtusAC/1.0",
        })

    def get_state(self) -> ACState:
        """Get the current state of the AC."""
        url = f"{self.BASE_URL}/api-enki-equation-airco-prod/v1/equation-airco/{self.node_id}/check-airconditioner-state"
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        value = data["lastReportedValue"]

        return ACState(
            target_temperature=value["targetTemperature"],
            current_temperature=value["currentTemperature"],
            operating_mode=OperatingMode(value["operatingMode"]),
            power=Power(value["power"]),
            fan_speed=FanSpeed(value["fanSpeed"]),
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

    def set_state(
        self,
        *,
        power: Optional[Power] = None,
        target_temperature: Optional[float] = None,
        operating_mode: Optional[OperatingMode] = None,
        fan_speed: Optional[FanSpeed] = None,
        health_mode: Optional[bool] = None,
        frost_protection_mode: Optional[bool] = None,
        self_clean_mode: Optional[bool] = None,
        quiet_mode: Optional[bool] = None,
        sleep_mode: Optional[bool] = None,
        swing_orientation: Optional[SwingOrientation] = None,
    ) -> bool:
        """Set the state of the AC.

        Only include parameters you want to change.

        Returns:
            True if the command was accepted (202 status).
        """
        url = f"{self.BASE_URL}/api-enki-equation-airco-prod/v1/equation-airco/{self.node_id}/change-airconditioner-state"

        payload = {
            "targetTemperature": target_temperature,
            "currentTemperature": None,
            "operatingMode": operating_mode.value if operating_mode else None,
            "power": power.value if power else None,
            "fanSpeed": fan_speed.value if fan_speed else None,
            "frostProtectionMode": frost_protection_mode if frost_protection_mode is not None else False,
            "selfCleanMode": self_clean_mode if self_clean_mode is not None else False,
            "healthMode": health_mode if health_mode is not None else False,
            "quietMode": quiet_mode if quiet_mode is not None else False,
            "sleepMode": sleep_mode if sleep_mode is not None else False,
            "swingOrientation": (
                {"horizontal": swing_orientation.horizontal, "vertical": swing_orientation.vertical}
                if swing_orientation
                else None
            ),
        }

        response = self.session.post(url, json=payload)
        return response.status_code == 202

    def turn_on(self) -> bool:
        """Turn the AC on."""
        return self.set_state(power=Power.ON)

    def turn_off(self) -> bool:
        """Turn the AC off."""
        return self.set_state(power=Power.OFF)

    def set_temperature(self, temperature: float) -> bool:
        """Set the target temperature."""
        return self.set_state(target_temperature=temperature)

    def set_mode(self, mode: OperatingMode) -> bool:
        """Set the operating mode."""
        return self.set_state(operating_mode=mode)

    def set_fan_speed(self, speed: FanSpeed) -> bool:
        """Set the fan speed."""
        return self.set_state(fan_speed=speed)

    def get_error(self) -> dict:
        """Get any error codes from the AC."""
        url = f"{self.BASE_URL}/api-enki-equation-airco-prod/v1/equation-airco/{self.node_id}/check-airconditioner-error"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def set_quiet_mode(self, enabled: bool) -> bool:
        """Enable or disable quiet mode."""
        return self.set_state(quiet_mode=enabled)

    def set_sleep_mode(self, enabled: bool) -> bool:
        """Enable or disable sleep mode."""
        return self.set_state(sleep_mode=enabled)

    def set_health_mode(self, enabled: bool) -> bool:
        """Enable or disable health/ionizer mode."""
        return self.set_state(health_mode=enabled)

    def set_frost_protection(self, enabled: bool) -> bool:
        """Enable or disable frost protection mode."""
        return self.set_state(frost_protection_mode=enabled)

    def set_self_clean(self, enabled: bool) -> bool:
        """Enable or disable self-cleaning mode."""
        return self.set_state(self_clean_mode=enabled)


# Example usage
if __name__ == "__main__":
    # These values need to be obtained from the Enki app or API
    ACCESS_TOKEN = "your_jwt_token_here"
    HOME_ID = "your_home_id"
    NODE_ID = "your_node_id"

    ac = EquationVirtusAC(ACCESS_TOKEN, HOME_ID, NODE_ID)

    # Get current state
    state = ac.get_state()
    print(f"Current temperature: {state.current_temperature}°C")
    print(f"Target temperature: {state.target_temperature}°C")
    print(f"Power: {state.power.value}")
    print(f"Mode: {state.operating_mode.value}")
    print(f"Fan speed: {state.fan_speed.value}")

    # Turn on and set to cooling mode at 24°C
    # ac.turn_on()
    # ac.set_mode(OperatingMode.COOL)
    # ac.set_temperature(24.0)
