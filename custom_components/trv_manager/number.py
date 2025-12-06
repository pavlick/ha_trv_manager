"""Number entities for TRV Manager."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_I_GAIN,
    CONF_P_GAIN,
    DOMAIN,
    ENTITY_ID_I_GAIN,
    ENTITY_ID_P_GAIN,
    MAX_I_GAIN,
    MAX_P_GAIN,
    MIN_I_GAIN,
    MIN_P_GAIN,
)
from .coordinator import TRVManagerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRV Manager number entities."""
    coordinator: TRVManagerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    # Get initial values from config or options
    p_gain = entry.options.get(CONF_P_GAIN, entry.data.get(CONF_P_GAIN))
    i_gain = entry.options.get(CONF_I_GAIN, entry.data.get(CONF_I_GAIN))

    entities = [
        TRVManagerPGainNumber(coordinator, entry, p_gain),
        TRVManagerIGainNumber(coordinator, entry, i_gain),
    ]

    async_add_entities(entities)


class TRVManagerPGainNumber(NumberEntity):
    """Number entity for P gain control."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_step = 0.1

    def __init__(
        self,
        coordinator: TRVManagerCoordinator,
        entry: ConfigEntry,
        initial_value: float,
    ) -> None:
        """Initialize the P gain number."""
        self._coordinator = coordinator
        self._entry = entry
        self._attr_native_value = initial_value
        self._attr_native_min_value = MIN_P_GAIN
        self._attr_native_max_value = MAX_P_GAIN
        
        self._attr_name = "P Gain"
        self._attr_unique_id = f"{entry.entry_id}{ENTITY_ID_P_GAIN}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "TRV Manager",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the P gain."""
        self._attr_native_value = value
        self._coordinator.update_gains(p_gain=value)
        self.async_write_ha_state()
        
        _LOGGER.info("P gain updated to %f", value)


class TRVManagerIGainNumber(NumberEntity):
    """Number entity for I gain control."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_step = 0.01

    def __init__(
        self,
        coordinator: TRVManagerCoordinator,
        entry: ConfigEntry,
        initial_value: float,
    ) -> None:
        """Initialize the I gain number."""
        self._coordinator = coordinator
        self._entry = entry
        self._attr_native_value = initial_value
        self._attr_native_min_value = MIN_I_GAIN
        self._attr_native_max_value = MAX_I_GAIN
        
        self._attr_name = "I Gain"
        self._attr_unique_id = f"{entry.entry_id}{ENTITY_ID_I_GAIN}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "TRV Manager",
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the I gain."""
        self._attr_native_value = value
        self._coordinator.update_gains(i_gain=value)
        self.async_write_ha_state()
        
        _LOGGER.info("I gain updated to %f", value)

