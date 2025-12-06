"""The TRV Manager integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_I_GAIN,
    CONF_P_GAIN,
    CONF_REFERENCE_TEMP_ENTITY,
    CONF_TARGET_TEMP_ENTITY,
    CONF_TRV_ENTITY,
    CONF_TRV_DWELL_TIME,
    CONF_VALVE_POSITION_ENTITY,
    DEFAULT_I_GAIN,
    DEFAULT_P_GAIN,
    DEFAULT_TRV_DWELL_TIME,
    DOMAIN,
)
from .coordinator import TRVManagerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRV Manager from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration values (check options first, then data)
    p_gain = entry.options.get(CONF_P_GAIN, entry.data.get(CONF_P_GAIN, DEFAULT_P_GAIN))
    i_gain = entry.options.get(CONF_I_GAIN, entry.data.get(CONF_I_GAIN, DEFAULT_I_GAIN))
    trv_dwell_time = entry.options.get(
        CONF_TRV_DWELL_TIME, entry.data.get(CONF_TRV_DWELL_TIME, DEFAULT_TRV_DWELL_TIME)
    )

    # Create coordinator
    coordinator = TRVManagerCoordinator(
        hass,
        entry.entry_id,
        entry.data[CONF_TRV_ENTITY],
        entry.data[CONF_REFERENCE_TEMP_ENTITY],
        entry.data[CONF_TARGET_TEMP_ENTITY],
        entry.data.get(CONF_VALVE_POSITION_ENTITY),
        p_gain,
        i_gain,
        trv_dwell_time,
    )

    # Set up the coordinator
    await coordinator.async_setup()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info(
        "TRV Manager initialized for %s (TRV: %s)",
        entry.data[CONF_NAME],
        entry.data[CONF_TRV_ENTITY],
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Shutdown coordinator
        coordinator: TRVManagerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        await coordinator.async_shutdown()

        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

