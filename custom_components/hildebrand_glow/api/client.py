"""
API Client for Glowmarkt API (Hildebrand Glow).

This module provides the API client for communicating with the Glowmarkt API
to retrieve smart meter energy data (electricity and gas consumption/cost).

API Documentation: https://api.glowmarkt.com/api-docs/
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import socket
from typing import Any

import aiohttp

from custom_components.hildebrand_glow.const import API_URL, APPLICATION_ID, LOGGER


class HildebrandGlowEnergyMonitorApiClientError(Exception):
    """Base exception to indicate a general API error."""


class HildebrandGlowEnergyMonitorApiClientCommunicationError(
    HildebrandGlowEnergyMonitorApiClientError,
):
    """Exception to indicate a communication error with the API."""


class HildebrandGlowEnergyMonitorApiClientAuthenticationError(
    HildebrandGlowEnergyMonitorApiClientError,
):
    """Exception to indicate an authentication error with the API."""


class HildebrandGlowEnergyMonitorApiClient:
    """
    API Client for Glowmarkt/Hildebrand Glow energy monitoring.

    This client handles authentication and communication with the Glowmarkt API
    to retrieve smart meter data including electricity and gas consumption,
    costs, and tariff information.

    Attributes:
        _username: The username (email) for Glowmarkt account.
        _password: The password for Glowmarkt account.
        _session: The aiohttp ClientSession for making requests.
        _token: The authentication token from the API.
        _token_expiry: When the token expires (UTC).

    """

    # Token validity period (Glowmarkt tokens typically last 1 hour, refresh 5 min before)
    TOKEN_LIFETIME_SECONDS = 55 * 60  # 55 minutes

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """
        Initialize the API Client with credentials.

        Args:
            username: The username (email) for Glowmarkt account.
            password: The password for Glowmarkt account.
            session: The aiohttp ClientSession to use for requests.

        """
        self._username = username
        self._password = password
        self._session = session
        self._token: str | None = None
        self._token_expiry: datetime | None = None

    async def async_authenticate(self) -> str:
        """
        Authenticate with the Glowmarkt API and obtain a token.

        Returns:
            The authentication token.

        Raises:
            HildebrandGlowEnergyMonitorApiClientAuthenticationError: If authentication fails.
            HildebrandGlowEnergyMonitorApiClientCommunicationError: If communication fails.

        """
        try:
            LOGGER.debug("Authenticating with Glowmarkt API for user: %s", self._username)
            async with asyncio.timeout(10):
                response = await self._session.post(
                    f"{API_URL}/auth",
                    headers={
                        "Content-Type": "application/json",
                        "applicationId": APPLICATION_ID,
                    },
                    json={
                        "username": self._username,
                        "password": self._password,
                    },
                )

                LOGGER.debug("Auth response status: %s", response.status)

                if response.status in (401, 403):
                    msg = "Invalid credentials"
                    raise HildebrandGlowEnergyMonitorApiClientAuthenticationError(msg)  # noqa: TRY301

                response.raise_for_status()
                data = await response.json()

                if not data.get("valid"):
                    msg = "Authentication failed: invalid response"
                    raise HildebrandGlowEnergyMonitorApiClientAuthenticationError(msg)  # noqa: TRY301

                self._token = data.get("token")
                if not self._token:
                    msg = "Authentication failed: no token received"
                    raise HildebrandGlowEnergyMonitorApiClientAuthenticationError(msg)  # noqa: TRY301

                # Set token expiry time
                self._token_expiry = datetime.now(tz=UTC) + timedelta(seconds=self.TOKEN_LIFETIME_SECONDS)
                LOGGER.debug(
                    "Authentication successful, token obtained (expires at %s)",
                    self._token_expiry.isoformat(),
                )
                return self._token

        except HildebrandGlowEnergyMonitorApiClientAuthenticationError:
            raise
        except TimeoutError as exception:
            msg = f"Timeout during authentication - {exception}"
            raise HildebrandGlowEnergyMonitorApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Communication error during authentication - {exception}"
            raise HildebrandGlowEnergyMonitorApiClientCommunicationError(msg) from exception

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire."""
        if not self._token or not self._token_expiry:
            return True
        # Consider expired if less than 1 minute remaining
        return datetime.now(tz=UTC) >= self._token_expiry - timedelta(minutes=1)

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if self._is_token_expired():
            LOGGER.debug("Token missing or expired, authenticating...")
            await self.async_authenticate()

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers with authentication token."""
        return {
            "Content-Type": "application/json",
            "applicationId": APPLICATION_ID,
            "token": self._token or "",
        }

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (get, post, etc.).
            endpoint: API endpoint path.
            params: Optional query parameters.
            data: Optional request body data.

        Returns:
            The JSON response from the API.

        Raises:
            HildebrandGlowEnergyMonitorApiClientAuthenticationError: If authentication fails.
            HildebrandGlowEnergyMonitorApiClientCommunicationError: If communication fails.
            HildebrandGlowEnergyMonitorApiClientError: For other API errors.

        """
        await self._ensure_authenticated()

        try:
            LOGGER.debug("API request: %s %s params=%s", method.upper(), endpoint, params)
            async with asyncio.timeout(30):
                response = await self._session.request(
                    method=method,
                    url=f"{API_URL}/{endpoint}",
                    headers=self._get_auth_headers(),
                    params=params,
                    json=data,
                )

                LOGGER.debug("API response status: %s for %s", response.status, endpoint)

                if response.status in (401, 403):
                    # Token may have expired, try re-authenticating
                    LOGGER.debug("Token expired, re-authenticating...")
                    self._token = None
                    await self.async_authenticate()
                    # Retry the request
                    response = await self._session.request(
                        method=method,
                        url=f"{API_URL}/{endpoint}",
                        headers=self._get_auth_headers(),
                        params=params,
                        json=data,
                    )
                    if response.status in (401, 403):
                        msg = "Authentication failed after token refresh"
                        raise HildebrandGlowEnergyMonitorApiClientAuthenticationError(msg)  # noqa: TRY301

                response.raise_for_status()
                result = await response.json()
                LOGGER.debug(
                    "API response for %s: %s items", endpoint, len(result) if isinstance(result, list) else "dict"
                )
                return result

        except HildebrandGlowEnergyMonitorApiClientAuthenticationError:
            raise
        except TimeoutError as exception:
            msg = f"Timeout fetching data from {endpoint} - {exception}"
            raise HildebrandGlowEnergyMonitorApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Communication error with {endpoint} - {exception}"
            raise HildebrandGlowEnergyMonitorApiClientCommunicationError(msg) from exception
        except Exception as exception:
            msg = f"Unexpected error with {endpoint} - {exception}"
            raise HildebrandGlowEnergyMonitorApiClientError(msg) from exception

    async def async_get_virtual_entities(self) -> list[dict[str, Any]]:
        """
        Get all virtual entities (smart meters) for the user.

        Returns:
            List of virtual entity dictionaries containing:
            - veId: Virtual entity ID
            - name: Name of the meter
            - postalCode: Location postal code

        """
        return await self._api_request("get", "virtualentity")

    async def async_get_resources(self, virtual_entity_id: str) -> list[dict[str, Any]]:
        """
        Get resources for a virtual entity.

        Args:
            virtual_entity_id: The virtual entity ID (veId).

        Returns:
            List of resource dictionaries containing:
            - resourceId: Resource ID
            - classifier: Resource type (e.g., "electricity.consumption")
            - name: Resource name
            - baseUnit: Unit of measurement (e.g., "kWh", "pence")

        """
        response = await self._api_request("get", f"virtualentity/{virtual_entity_id}/resources")
        return response.get("resources", [])

    async def async_get_readings(
        self,
        resource_id: str,
        from_datetime: datetime,
        to_datetime: datetime,
        period: str = "P1D",
        function: str = "sum",
    ) -> dict[str, Any]:
        """
        Get meter readings for a resource.

        Args:
            resource_id: The resource ID.
            from_datetime: Start datetime (UTC).
            to_datetime: End datetime (UTC).
            period: Aggregation period (P1D, P1W, P1M, PT30M, etc.).
            function: Aggregation function (sum, mean, etc.).

        Returns:
            Dictionary containing:
            - units: Unit of measurement
            - data: List of [timestamp, value] pairs

        """
        params = {
            "from": from_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "to": to_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            "period": period,
            "function": function,
            "offset": "0",
        }
        return await self._api_request("get", f"resource/{resource_id}/readings", params=params)

    async def async_get_tariff(self, resource_id: str) -> dict[str, Any]:
        """
        Get tariff information for a resource.

        Args:
            resource_id: The resource ID.

        Returns:
            Dictionary containing tariff data including:
            - currentRates: {rate, standingCharge} in pence

        """
        return await self._api_request("get", f"resource/{resource_id}/tariff")

    async def async_get_current(self, resource_id: str) -> dict[str, Any]:
        """
        Get current real-time reading for a resource.

        This returns the most recent instantaneous reading from the smart meter,
        typically used for real-time power monitoring (kW for electricity).

        Args:
            resource_id: The resource ID.

        Returns:
            Dictionary containing:
            - data: List with single [timestamp, value] pair for current reading
            - units: Unit of measurement

        """
        return await self._api_request("get", f"resource/{resource_id}/current")

    async def async_catchup(self, resource_id: str) -> dict[str, Any]:
        """
        Request DCC to pull latest data for a resource.

        This triggers the smart meter to send its latest readings.

        Args:
            resource_id: The resource ID.

        Returns:
            API response confirming the catchup request.

        """
        return await self._api_request("get", f"resource/{resource_id}/catchup")

    async def async_get_data(self) -> dict[str, Any]:
        """
        Get all energy data for the user.

        This fetches virtual entities, resources, readings, and tariffs
        for all available smart meters.

        Returns:
            Dictionary containing all energy data structured by meter.

        """
        result: dict[str, Any] = {
            "virtual_entities": [],
            "meters": {},
        }

        # Get all virtual entities (smart meters)
        virtual_entities = await self.async_get_virtual_entities()
        result["virtual_entities"] = virtual_entities

        # For each virtual entity, get resources and readings
        for ve in virtual_entities:
            ve_id = ve.get("veId")
            if not ve_id:
                continue

            LOGGER.debug("Processing virtual entity: %s", ve_id)
            resources = await self.async_get_resources(ve_id)
            LOGGER.debug("Found %d resources for %s", len(resources), ve_id)

            meter_data: dict[str, Any] = {
                "virtual_entity": ve,
                "resources": resources,
                "readings": {},
                "current": {},
                "tariffs": {},
            }

            # Calculate time ranges for readings
            now = datetime.now(tz=UTC)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)

            for resource in resources:
                resource_id = resource.get("resourceId")
                classifier = resource.get("classifier", "")

                if not resource_id:
                    continue

                LOGGER.debug("Fetching data for resource: %s (%s)", resource_id, classifier)

                # Get current/recent reading using PT1M resolution (for consumption resources only)
                if "cost" not in classifier:
                    try:
                        # Use readings endpoint with 1-minute resolution for last 5 minutes
                        recent_start = now - timedelta(minutes=5)
                        LOGGER.debug(
                            "Fetching PT1M readings for %s from %s to %s",
                            classifier,
                            recent_start.isoformat(),
                            now.isoformat(),
                        )
                        current = await self.async_get_readings(
                            resource_id,
                            recent_start,
                            now,
                            period="PT1M",
                        )
                        meter_data["current"][classifier] = current
                        data_points = len(current.get("data", []))
                        LOGGER.debug("PT1M readings for %s: %d data points", classifier, data_points)
                    except HildebrandGlowEnergyMonitorApiClientError as err:
                        LOGGER.debug("Failed to get PT1M readings for %s: %s", classifier, err)

                # Get today's readings
                try:
                    today_readings = await self.async_get_readings(
                        resource_id,
                        today_start,
                        now,
                        period="P1D",
                    )
                    meter_data["readings"][f"{classifier}_today"] = today_readings
                except HildebrandGlowEnergyMonitorApiClientError:
                    pass  # Skip if readings unavailable

                # Get this week's readings
                try:
                    week_readings = await self.async_get_readings(
                        resource_id,
                        week_start,
                        now,
                        period="P1W",
                    )
                    meter_data["readings"][f"{classifier}_week"] = week_readings
                except HildebrandGlowEnergyMonitorApiClientError:
                    pass

                # Get this month's readings
                try:
                    month_readings = await self.async_get_readings(
                        resource_id,
                        month_start,
                        now,
                        period="P1M",
                    )
                    meter_data["readings"][f"{classifier}_month"] = month_readings
                except HildebrandGlowEnergyMonitorApiClientError:
                    pass

                # Get tariff if it's a consumption resource (not cost)
                if "cost" not in classifier:
                    try:
                        tariff = await self.async_get_tariff(resource_id)
                        meter_data["tariffs"][classifier] = tariff
                    except HildebrandGlowEnergyMonitorApiClientError:
                        pass

            result["meters"][ve_id] = meter_data

        return result
