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
    CONF_DEVICE_ID,
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
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinators = entry_data["coordinators"]

    entities = []

    # Create P and I gain entities for each device
    for device_id, device_data in coordinators.items():
        coordinator: TRVManagerCoordinator = device_data["coordinator"]
        device_name = device_data["device_name"]

        entities.extend([
            TRVManagerPGainNumber(coordinator, entry, device_id, device_name),
            TRVManagerIGainNumber(coordinator, entry, device_id, device_name),
        ])

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
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize the P gain number."""
        self._coordinator = coordinator
        self._entry = entry
        self._device_id = device_id
        self._attr_native_value = coordinator._p_gain
        self._attr_native_min_value = MIN_P_GAIN
        self._attr_native_max_value = MAX_P_GAIN
        
        self._attr_name = "P Gain"
        self._attr_unique_id = f"{entry.entry_id}_{device_id}{ENTITY_ID_P_GAIN}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}_{device_id}")},
            "name": device_name,
            "manufacturer": "TRV Manager",
            "model": "TRV Controller",
            "via_device": (DOMAIN, entry.entry_id),
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the P gain."""
        self._attr_native_value = value
        self._coordinator.update_gains(p_gain=value)
        self.async_write_ha_state()
        
        _LOGGER.info("P gain updated to %f for device %s", value, self._device_id)


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
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize the I gain number."""
        self._coordinator = coordinator
        self._entry = entry
        self._device_id = device_id
        self._attr_native_value = coordinator._i_gain
        self._attr_native_min_value = MIN_I_GAIN
        self._attr_native_max_value = MAX_I_GAIN
        
        self._attr_name = "I Gain"
        self._attr_unique_id = f"{entry.entry_id}_{device_id}{ENTITY_ID_I_GAIN}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}_{device_id}")},
            "name": device_name,
            "manufacturer": "TRV Manager",
            "model": "TRV Controller",
            "via_device": (DOMAIN, entry.entry_id),
        }

    async def async_set_native_value(self, value: float) -> None:
        """Update the I gain."""
        self._attr_native_value = value
        self._coordinator.update_gains(i_gain=value)
        self.async_write_ha_state()
        
        _LOGGER.info("I gain updated to %f for device %s", value, self._device_id)
