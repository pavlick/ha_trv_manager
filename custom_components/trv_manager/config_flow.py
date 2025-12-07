"""Config flow for TRV Manager integration."""
from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_TRV_ENTITY,
    CONF_REFERENCE_TEMP_ENTITY,
    CONF_TARGET_TEMP_ENTITY,
    CONF_VALVE_POSITION_ENTITY,
    CONF_DEVICES,
    CONF_P_GAIN,
    CONF_I_GAIN,
    CONF_TRV_DWELL_TIME,
    CONF_VALVE_STEP,
    DEFAULT_P_GAIN,
    DEFAULT_I_GAIN,
    DEFAULT_TRV_DWELL_TIME,
    DEFAULT_VALVE_STEP,
    MIN_P_GAIN,
    MAX_P_GAIN,
    MIN_I_GAIN,
    MAX_I_GAIN,
)


class TRVManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRV Manager."""

    VERSION = 2  # Bumped version for new hub structure

    def __init__(self) -> None:
        """Initialize config flow."""
        self._hub_data: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step - create hub."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store hub configuration
            self._hub_data = user_input
            
            # Set unique ID based on hub name
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            
            # Move to device addition step
            return await self.async_step_add_device()

        # Build the hub configuration schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="TRV Manager Hub"): cv.string,
                vol.Required(CONF_REFERENCE_TEMP_ENTITY): selector.EntitySelector(
                    {"domain": "sensor", "device_class": "temperature"}
                ),
                vol.Required(CONF_TARGET_TEMP_ENTITY): selector.EntitySelector(
                    {"domain": ["sensor", "input_number", "number"]}
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "description": "Create a hub that manages multiple TRV devices. "
                "All devices will share the same reference and target temperature."
            },
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle adding a TRV device to the hub."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Generate unique device ID
            device_id = str(uuid.uuid4())
            
            # Check if TRV entity is already used in this hub
            if any(d[CONF_TRV_ENTITY] == user_input[CONF_TRV_ENTITY] for d in self._devices):
                errors["base"] = "trv_already_added"
            else:
                # Add device configuration
                device_config = {
                    CONF_DEVICE_ID: device_id,
                    CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME],
                    CONF_TRV_ENTITY: user_input[CONF_TRV_ENTITY],
                    CONF_VALVE_POSITION_ENTITY: user_input.get(CONF_VALVE_POSITION_ENTITY),
                    CONF_P_GAIN: user_input.get(CONF_P_GAIN, DEFAULT_P_GAIN),
                    CONF_I_GAIN: user_input.get(CONF_I_GAIN, DEFAULT_I_GAIN),
                    CONF_TRV_DWELL_TIME: user_input.get(CONF_TRV_DWELL_TIME, DEFAULT_TRV_DWELL_TIME),
                    CONF_VALVE_STEP: user_input.get(CONF_VALVE_STEP, DEFAULT_VALVE_STEP),
                }
                self._devices.append(device_config)
                
                # Ask if user wants to add another device
                return await self.async_step_add_another()

        # Build device configuration schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_NAME, default="TRV Device"): cv.string,
                vol.Required(CONF_TRV_ENTITY): selector.EntitySelector(
                    {"domain": "climate"}
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
                vol.Optional(
                    CONF_TRV_DWELL_TIME,
                    default=DEFAULT_TRV_DWELL_TIME,
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=300)),
                vol.Optional(
                    CONF_VALVE_STEP,
                    default=DEFAULT_VALVE_STEP,
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
            }
        )

        return self.async_show_form(
            step_id="add_device",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "hub_name": self._hub_data[CONF_NAME],
                "devices_count": str(len(self._devices)),
            },
        )

    async def async_step_add_another(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Ask if user wants to add another device."""
        if user_input is not None:
            if user_input.get("add_another"):
                return await self.async_step_add_device()
            
            # User is done, create the entry
            if not self._devices:
                # Need at least one device
                return await self.async_step_add_device()
            
            return self.async_create_entry(
                title=self._hub_data[CONF_NAME],
                data={
                    **self._hub_data,
                    CONF_DEVICES: self._devices,
                },
            )

        return self.async_show_form(
            step_id="add_another",
            data_schema=vol.Schema(
                {
                    vol.Required("add_another", default=False): cv.boolean,
                }
            ),
            description_placeholders={
                "devices_count": str(len(self._devices)),
            },
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

    def __init__(self) -> None:
        """Initialize options flow."""
        self._current_device_id: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options - choose what to configure."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["configure_hub", "manage_devices"],
        )

    async def async_step_configure_hub(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure hub-level settings."""
        if user_input is not None:
            # Update hub settings
            new_data = {**self.config_entry.data}
            new_data[CONF_REFERENCE_TEMP_ENTITY] = user_input[CONF_REFERENCE_TEMP_ENTITY]
            new_data[CONF_TARGET_TEMP_ENTITY] = user_input[CONF_TARGET_TEMP_ENTITY]
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            return self.async_create_entry(title="", data={})

        current_data = self.config_entry.data

        data_schema = vol.Schema(
            {
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
            }
        )

        return self.async_show_form(step_id="configure_hub", data_schema=data_schema)

    async def async_step_manage_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage devices."""
        return self.async_show_menu(
            step_id="manage_devices",
            menu_options=["add_device", "edit_device", "remove_device"],
        )

    async def async_step_add_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Add a new device to the hub."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if TRV entity is already used
            current_devices = self.config_entry.data.get(CONF_DEVICES, [])
            if any(d[CONF_TRV_ENTITY] == user_input[CONF_TRV_ENTITY] for d in current_devices):
                errors["base"] = "trv_already_added"
            else:
                # Add new device
                device_id = str(uuid.uuid4())
                new_device = {
                    CONF_DEVICE_ID: device_id,
                    CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME],
                    CONF_TRV_ENTITY: user_input[CONF_TRV_ENTITY],
                    CONF_VALVE_POSITION_ENTITY: user_input.get(CONF_VALVE_POSITION_ENTITY),
                    CONF_P_GAIN: user_input.get(CONF_P_GAIN, DEFAULT_P_GAIN),
                    CONF_I_GAIN: user_input.get(CONF_I_GAIN, DEFAULT_I_GAIN),
                    CONF_TRV_DWELL_TIME: user_input.get(CONF_TRV_DWELL_TIME, DEFAULT_TRV_DWELL_TIME),
                    CONF_VALVE_STEP: user_input.get(CONF_VALVE_STEP, DEFAULT_VALVE_STEP),
                }
                
                new_data = {**self.config_entry.data}
                new_data[CONF_DEVICES] = current_devices + [new_device]
                
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                )
                return self.async_create_entry(title="", data={})

        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_NAME): cv.string,
                vol.Required(CONF_TRV_ENTITY): selector.EntitySelector(
                    {"domain": "climate"}
                ),
                vol.Optional(CONF_VALVE_POSITION_ENTITY): selector.EntitySelector(
                    {"domain": ["number", "input_number"]}
                ),
                vol.Optional(CONF_P_GAIN, default=DEFAULT_P_GAIN): vol.All(
                    vol.Coerce(float), vol.Range(min=MIN_P_GAIN, max=MAX_P_GAIN)
                ),
                vol.Optional(CONF_I_GAIN, default=DEFAULT_I_GAIN): vol.All(
                    vol.Coerce(float), vol.Range(min=MIN_I_GAIN, max=MAX_I_GAIN)
                ),
                vol.Optional(CONF_TRV_DWELL_TIME, default=DEFAULT_TRV_DWELL_TIME): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=300)
                ),
                vol.Optional(CONF_VALVE_STEP, default=DEFAULT_VALVE_STEP): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=20)
                ),
            }
        )

        return self.async_show_form(
            step_id="add_device",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_edit_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select a device to edit."""
        current_devices = self.config_entry.data.get(CONF_DEVICES, [])
        
        if not current_devices:
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            self._current_device_id = user_input["device"]
            return await self.async_step_edit_device_settings()

        # Build device selection
        device_options = {
            device[CONF_DEVICE_ID]: device[CONF_DEVICE_NAME]
            for device in current_devices
        }

        data_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(device_options),
            }
        )

        return self.async_show_form(
            step_id="edit_device",
            data_schema=data_schema,
        )

    async def async_step_edit_device_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Edit device settings."""
        current_devices = self.config_entry.data.get(CONF_DEVICES, [])
        device = next(
            (d for d in current_devices if d[CONF_DEVICE_ID] == self._current_device_id),
            None,
        )

        if device is None:
            return self.async_abort(reason="device_not_found")

        if user_input is not None:
            # Update device
            updated_devices = [
                {
                    **d,
                    CONF_DEVICE_NAME: user_input[CONF_DEVICE_NAME],
                    CONF_TRV_ENTITY: user_input[CONF_TRV_ENTITY],
                    CONF_VALVE_POSITION_ENTITY: user_input.get(CONF_VALVE_POSITION_ENTITY),
                    CONF_P_GAIN: user_input.get(CONF_P_GAIN, DEFAULT_P_GAIN),
                    CONF_I_GAIN: user_input.get(CONF_I_GAIN, DEFAULT_I_GAIN),
                    CONF_TRV_DWELL_TIME: user_input.get(CONF_TRV_DWELL_TIME, DEFAULT_TRV_DWELL_TIME),
                    CONF_VALVE_STEP: user_input.get(CONF_VALVE_STEP, DEFAULT_VALVE_STEP),
                }
                if d[CONF_DEVICE_ID] == self._current_device_id
                else d
                for d in current_devices
            ]

            new_data = {**self.config_entry.data}
            new_data[CONF_DEVICES] = updated_devices

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_NAME, default=device[CONF_DEVICE_NAME]): cv.string,
                vol.Required(CONF_TRV_ENTITY, default=device[CONF_TRV_ENTITY]): selector.EntitySelector(
                    {"domain": "climate"}
                ),
                vol.Optional(
                    CONF_VALVE_POSITION_ENTITY,
                    default=device.get(CONF_VALVE_POSITION_ENTITY),
                ): selector.EntitySelector({"domain": ["number", "input_number"]}),
                vol.Optional(
                    CONF_P_GAIN,
                    default=device.get(CONF_P_GAIN, DEFAULT_P_GAIN),
                ): vol.All(vol.Coerce(float), vol.Range(min=MIN_P_GAIN, max=MAX_P_GAIN)),
                vol.Optional(
                    CONF_I_GAIN,
                    default=device.get(CONF_I_GAIN, DEFAULT_I_GAIN),
                ): vol.All(vol.Coerce(float), vol.Range(min=MIN_I_GAIN, max=MAX_I_GAIN)),
                vol.Optional(
                    CONF_TRV_DWELL_TIME,
                    default=device.get(CONF_TRV_DWELL_TIME, DEFAULT_TRV_DWELL_TIME),
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=300)),
                vol.Optional(
                    CONF_VALVE_STEP,
                    default=device.get(CONF_VALVE_STEP, DEFAULT_VALVE_STEP),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
            }
        )

        return self.async_show_form(
            step_id="edit_device_settings",
            data_schema=data_schema,
        )

    async def async_step_remove_device(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Remove a device from the hub."""
        current_devices = self.config_entry.data.get(CONF_DEVICES, [])
        
        if not current_devices:
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            device_id = user_input["device"]
            
            # Remove device
            updated_devices = [
                d for d in current_devices if d[CONF_DEVICE_ID] != device_id
            ]

            if not updated_devices:
                return self.async_abort(reason="cannot_remove_last_device")

            new_data = {**self.config_entry.data}
            new_data[CONF_DEVICES] = updated_devices

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            return self.async_create_entry(title="", data={})

        # Build device selection
        device_options = {
            device[CONF_DEVICE_ID]: device[CONF_DEVICE_NAME]
            for device in current_devices
        }

        data_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(device_options),
            }
        )

        return self.async_show_form(
            step_id="remove_device",
            data_schema=data_schema,
        )
