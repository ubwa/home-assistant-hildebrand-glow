"""
Credential validators.

Validation functions for user credentials and authentication.

When this file grows, consider splitting into:
- credentials.py: Basic credential validation
- oauth.py: OAuth-specific validation
- api_auth.py: API authentication methods
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.hildebrand_glow.api import HildebrandGlowEnergyMonitorApiClient
from homeassistant.helpers.aiohttp_client import async_create_clientsession

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def validate_credentials(hass: HomeAssistant, username: str, password: str) -> None:
    """
    Validate user credentials by testing API authentication.

    This authenticates against the Glowmarkt API to verify the credentials
    are valid before storing them in the config entry.

    Args:
        hass: Home Assistant instance.
        username: The username (email) for Glowmarkt account.
        password: The password for Glowmarkt account.

    Raises:
        HildebrandGlowEnergyMonitorApiClientAuthenticationError: If credentials are invalid.
        HildebrandGlowEnergyMonitorApiClientCommunicationError: If communication fails.
        HildebrandGlowEnergyMonitorApiClientError: For other API errors.

    """
    client = HildebrandGlowEnergyMonitorApiClient(
        username=username,
        password=password,
        session=async_create_clientsession(hass),
    )
    # Authenticate to verify credentials are valid
    await client.async_authenticate()


__all__ = [
    "validate_credentials",
]
