"""Sensor entities for TRV Manager diagnostics."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENTITY_ID_ERROR,
    ENTITY_ID_INTEGRATOR,
    ENTITY_ID_TEMP_ADJUSTMENT,
    ENTITY_ID_VALVE_OUTPUT,
)
from .coordinator import TRVManagerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRV Manager sensor entities."""
    coordinator: TRVManagerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        TRVManagerErrorSensor(coordinator, entry),
        TRVManagerIntegratorSensor(coordinator, entry),
        TRVManagerTempAdjustmentSensor(coordinator, entry),
        TRVManagerValveOutputSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class TRVManagerErrorSensor(CoordinatorEntity[TRVManagerCoordinator], SensorEntity):
    """Sensor for temperature error (target - reference)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: TRVManagerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the error sensor."""
        super().__init__(coordinator)
        self._attr_name = "Temperature Error"
        self._attr_unique_id = f"{entry.entry_id}{ENTITY_ID_ERROR}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "TRV Manager",
        }

    @property
    def native_value(self) -> float | None:
        """Return the temperature error."""
        return self.coordinator.data.get("error")


class TRVManagerIntegratorSensor(CoordinatorEntity[TRVManagerCoordinator], SensorEntity):
    """Sensor for PI controller integrator value."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: TRVManagerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the integrator sensor."""
        super().__init__(coordinator)
        self._attr_name = "Integrator Value"
        self._attr_unique_id = f"{entry.entry_id}{ENTITY_ID_INTEGRATOR}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "TRV Manager",
        }

    @property
    def native_value(self) -> float | None:
        """Return the integrator value."""
        return self.coordinator.data.get("integrator")


class TRVManagerTempAdjustmentSensor(CoordinatorEntity[TRVManagerCoordinator], SensorEntity):
    """Sensor for temperature adjustment applied to TRV."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: TRVManagerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the temperature adjustment sensor."""
        super().__init__(coordinator)
        self._attr_name = "Temperature Adjustment"
        self._attr_unique_id = f"{entry.entry_id}{ENTITY_ID_TEMP_ADJUSTMENT}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "TRV Manager",
        }

    @property
    def native_value(self) -> float | None:
        """Return the temperature adjustment."""
        return self.coordinator.data.get("temp_adjustment")


class TRVManagerValveOutputSensor(CoordinatorEntity[TRVManagerCoordinator], SensorEntity):
    """Sensor for PI controller valve position output."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: TRVManagerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the valve output sensor."""
        super().__init__(coordinator)
        self._attr_name = "Valve Position Output"
        self._attr_unique_id = f"{entry.entry_id}{ENTITY_ID_VALVE_OUTPUT}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "TRV Manager",
        }

    @property
    def native_value(self) -> int | None:
        """Return the valve position output."""
        return self.coordinator.data.get("valve_output")

