"""The TRV Manager integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_DEVICES,
    CONF_I_GAIN,
    CONF_P_GAIN,
    CONF_REFERENCE_TEMP_ENTITY,
    CONF_TARGET_TEMP_ENTITY,
    CONF_TRV_ENTITY,
    CONF_TRV_DWELL_TIME,
    CONF_VALVE_POSITION_ENTITY,
    CONF_VALVE_STEP,
    DEFAULT_I_GAIN,
    DEFAULT_P_GAIN,
    DEFAULT_TRV_DWELL_TIME,
    DEFAULT_VALVE_STEP,
    DOMAIN,
)
from .coordinator import TRVManagerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRV Manager from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get hub configuration (shared by all devices)
    reference_temp_entity = entry.data[CONF_REFERENCE_TEMP_ENTITY]
    target_temp_entity = entry.data[CONF_TARGET_TEMP_ENTITY]
    devices_config = entry.data.get(CONF_DEVICES, [])

    if not devices_config:
        _LOGGER.error("No devices configured for hub %s", entry.data[CONF_NAME])
        return False

    # Create hub device in device registry
    device_registry = dr.async_get(hass)
    hub_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data[CONF_NAME],
        manufacturer="TRV Manager",
        model="Hub",
    )

    # Store hub info and coordinators
    coordinators = {}

    # Create a coordinator for each device
    for device_config in devices_config:
        device_id = device_config[CONF_DEVICE_ID]
        device_name = device_config[CONF_DEVICE_NAME]
        trv_entity = device_config[CONF_TRV_ENTITY]
        valve_position_entity = device_config.get(CONF_VALVE_POSITION_ENTITY)
        
        # Get device-specific settings with defaults
        p_gain = device_config.get(CONF_P_GAIN, DEFAULT_P_GAIN)
        i_gain = device_config.get(CONF_I_GAIN, DEFAULT_I_GAIN)
        trv_dwell_time = device_config.get(CONF_TRV_DWELL_TIME, DEFAULT_TRV_DWELL_TIME)
        valve_step = device_config.get(CONF_VALVE_STEP, DEFAULT_VALVE_STEP)

        # Create coordinator for this device
        coordinator = TRVManagerCoordinator(
            hass,
            entry.entry_id,
            device_id,
            trv_entity,
            reference_temp_entity,
            target_temp_entity,
            valve_position_entity,
            p_gain,
            i_gain,
            trv_dwell_time,
            valve_step,
        )

        # Set up the coordinator
        await coordinator.async_setup()

        # Store coordinator
        coordinators[device_id] = {
            "coordinator": coordinator,
            "device_name": device_name,
            "trv_entity": trv_entity,
        }

        # Create device in device registry
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{entry.entry_id}_{device_id}")},
            name=device_name,
            manufacturer="TRV Manager",
            model="TRV Controller",
            via_device=(DOMAIN, entry.entry_id),  # Link to hub
        )

        _LOGGER.info(
            "TRV Manager device initialized: %s (TRV: %s)",
            device_name,
            trv_entity,
        )

    # Store data
    hass.data[DOMAIN][entry.entry_id] = {
        "hub_name": entry.data[CONF_NAME],
        "reference_temp_entity": reference_temp_entity,
        "target_temp_entity": target_temp_entity,
        "coordinators": coordinators,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for config changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info(
        "TRV Manager hub '%s' initialized with %d device(s)",
        entry.data[CONF_NAME],
        len(coordinators),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Shutdown all coordinators
        entry_data = hass.data[DOMAIN][entry.entry_id]
        for device_id, device_data in entry_data["coordinators"].items():
            coordinator: TRVManagerCoordinator = device_data["coordinator"]
            await coordinator.async_shutdown()

        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when configuration changes."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
