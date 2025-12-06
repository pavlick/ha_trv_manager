"""Config flow for TRV Manager integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_TRV_ENTITY,
    CONF_REFERENCE_TEMP_ENTITY,
    CONF_TARGET_TEMP_ENTITY,
    CONF_VALVE_POSITION_ENTITY,
    CONF_P_GAIN,
    CONF_I_GAIN,
    DEFAULT_P_GAIN,
    DEFAULT_I_GAIN,
    MIN_P_GAIN,
    MAX_P_GAIN,
    MIN_I_GAIN,
    MAX_I_GAIN,
)


class TRVManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRV Manager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate entities exist
            await self.async_set_unique_id(user_input[CONF_TRV_ENTITY])
            self._abort_if_unique_id_configured()

            # Create the entry
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        # Build the configuration schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="TRV Manager"): cv.string,
                vol.Required(CONF_TRV_ENTITY): selector.EntitySelector(
                    {"domain": "climate"}
                ),
                vol.Required(CONF_REFERENCE_TEMP_ENTITY): selector.EntitySelector(
                    {"domain": "sensor", "device_class": "temperature"}
                ),
                vol.Required(CONF_TARGET_TEMP_ENTITY): selector.EntitySelector(
                    {"domain": ["sensor", "input_number", "number"]}
                ),
                vol.Optional(CONF_VALVE_POSITION_ENTITY): selector.EntitySelector(
                    {"domain": ["number", "input_number"]}
                ),
                vol.Optional(
                    CONF_P_GAIN,
                    default=DEFAULT_P_GAIN,
                ): vol.All(vol.Coerce(float), vol.Range(min=MIN_P_GAIN, max=MAX_P_GAIN)),
                vol.Optional(
                    CONF_I_GAIN,
                    default=DEFAULT_I_GAIN,
                ): vol.All(vol.Coerce(float), vol.Range(min=MIN_I_GAIN, max=MAX_I_GAIN)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TRVManagerOptionsFlow()


class TRVManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for TRV Manager."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from config entry
        current_data = self.config_entry.data
        current_options = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_TRV_ENTITY,
                    default=current_data.get(CONF_TRV_ENTITY),
                ): selector.EntitySelector(
                    {"domain": "climate"}
                ),
                vol.Required(
                    CONF_REFERENCE_TEMP_ENTITY,
                    default=current_data.get(CONF_REFERENCE_TEMP_ENTITY),
                ): selector.EntitySelector(
                    {"domain": "sensor", "device_class": "temperature"}
                ),
                vol.Required(
                    CONF_TARGET_TEMP_ENTITY,
                    default=current_data.get(CONF_TARGET_TEMP_ENTITY),
                ): selector.EntitySelector(
                    {"domain": ["sensor", "input_number", "number"]}
                ),
                vol.Optional(
                    CONF_VALVE_POSITION_ENTITY,
                    default=current_data.get(CONF_VALVE_POSITION_ENTITY),
                ): selector.EntitySelector(
                    {"domain": ["number", "input_number"]}
                ),
                vol.Optional(
                    CONF_P_GAIN,
                    default=current_options.get(
                        CONF_P_GAIN, current_data.get(CONF_P_GAIN, DEFAULT_P_GAIN)
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=MIN_P_GAIN, max=MAX_P_GAIN)),
                vol.Optional(
                    CONF_I_GAIN,
                    default=current_options.get(
                        CONF_I_GAIN, current_data.get(CONF_I_GAIN, DEFAULT_I_GAIN)
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=MIN_I_GAIN, max=MAX_I_GAIN)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)

