"""
Options flow schemas.

Schemas for the options flow that allows users to modify settings
after initial configuration.

When adding many options, consider grouping them:
- basic_options.py: Common settings (update interval, debug mode)
- advanced_options.py: Advanced settings
- device_options.py: Device-specific settings
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from custom_components.hildebrand_glow.const import DEFAULT_ENABLE_DEBUGGING, DEFAULT_UPDATE_INTERVAL_MINUTES
from homeassistant.helpers import selector


def get_options_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """
    Get schema for options flow.

    Args:
        defaults: Optional dictionary of current option values.

    Returns:
        Voluptuous schema for options configuration.

    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Optional(
                "update_interval_minutes",
                default=defaults.get("update_interval_minutes", DEFAULT_UPDATE_INTERVAL_MINUTES),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=60,
                    step=1,
                    unit_of_measurement="min",
                    mode=selector.NumberSelectorMode.BOX,
                ),
            ),
            vol.Optional(
                "enable_debugging",
                default=defaults.get("enable_debugging", DEFAULT_ENABLE_DEBUGGING),
            ): selector.BooleanSelector(),
            vol.Optional(
                "custom_icon",
                default=defaults.get("custom_icon"),
            ): selector.IconSelector(),
        },
    )


__all__ = [
    "get_options_schema",
]
