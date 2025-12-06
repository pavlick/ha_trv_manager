"""Data update coordinator for TRV Manager."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN, SERVICE_SET_VALUE
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_I_GAIN,
    CONF_P_GAIN,
    CONF_REFERENCE_TEMP_ENTITY,
    CONF_TARGET_TEMP_ENTITY,
    CONF_TRV_ENTITY,
    CONF_VALVE_POSITION_ENTITY,
    CONF_ANTI_WINDUP_GAIN,
    DEFAULT_ANTI_WINDUP_GAIN,
    DOMAIN,
    MAX_TRV_TARGET_TEMP,
    MAX_VALVE_POSITION,
    MIN_TRV_TARGET_TEMP,
    MIN_VALVE_POSITION,
    VALVE_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class TRVManagerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage TRV control with PI controller."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        trv_entity: str,
        reference_temp_entity: str,
        target_temp_entity: str,
        valve_position_entity: str | None,
        p_gain: float,
        i_gain: float,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=None,  # We handle updates manually
        )

        self.trv_entity = trv_entity
        self.reference_temp_entity = reference_temp_entity
        self.target_temp_entity = target_temp_entity
        self.valve_position_entity = valve_position_entity
        
        self._p_gain = p_gain
        self._i_gain = i_gain
        self._anti_windup_gain = DEFAULT_ANTI_WINDUP_GAIN

        # PI controller state
        self._integrator: float = 0.0
        self._last_update: datetime | None = None
        self._last_error: float = 0.0
        self._startup_attempts: int = 0  # Track startup attempts

        # Data storage
        self.data: dict[str, Any] = {
            "error": 0.0,
            "integrator": 0.0,
            "temp_adjustment": 0.0,
            "valve_output": 0,  # Integer valve position
            "hvac_action": None,  # Current TRV hvac_action
            "reference_temp": None,
            "target_temp": None,
            "trv_temp": None,
        }

        # Listeners
        self._remove_listeners: list = []

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        # Track state changes for immediate updates
        self._remove_listeners.append(
            async_track_state_change_event(
                self.hass,
                [
                    self.reference_temp_entity,
                    self.target_temp_entity,
                    self.trv_entity,
                ],
                self._handle_state_change,
            )
        )

        # Track periodic valve updates (every minute)
        if self.valve_position_entity:
            self._remove_listeners.append(
                async_track_time_interval(
                    self.hass,
                    self._handle_valve_update,
                    VALVE_UPDATE_INTERVAL,
                )
            )

        # Initial update
        await self._async_update_data()

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        for remove_listener in self._remove_listeners:
            remove_listener()
        self._remove_listeners.clear()

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state changes of monitored entities."""
        self.hass.async_create_task(self._async_update_data())

    @callback
    def _handle_valve_update(self, now: datetime) -> None:
        """Handle periodic valve position updates."""
        self.hass.async_create_task(self._async_update_valve_only())

    def update_gains(self, p_gain: float | None = None, i_gain: float | None = None) -> None:
        """Update PI controller gains."""
        if p_gain is not None:
            self._p_gain = p_gain
            _LOGGER.debug("Updated P gain to %f", p_gain)
        
        if i_gain is not None:
            self._i_gain = i_gain
            _LOGGER.debug("Updated I gain to %f", i_gain)

    def _get_float_state(self, entity_id: str) -> float | None:
        """Get numeric state value from entity."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        
        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not convert state of %s to float: %s", entity_id, state.state)
            return None

    def _calculate_temperature_compensation(
        self, target_temp: float, reference_temp: float, trv_temp: float
    ) -> float:
        """Calculate temperature compensation for TRV.
        
        Compensates for TRV's proximity to the radiator.
        Formula: adjusted_target = target + (trv_temp - reference_temp)
        """
        compensation = trv_temp - reference_temp
        adjusted_target = target_temp + compensation
        
        _LOGGER.debug(
            "Temperature compensation: target=%f, ref=%f, trv=%f, compensation=%f, adjusted=%f",
            target_temp, reference_temp, trv_temp, compensation, adjusted_target
        )
        
        return adjusted_target

    def _update_pi_controller(self, error: float, dt: float) -> int:
        """Update PI controller and return valve position output (0-100).
        
        Uses back-calculation anti-windup to prevent integrator windup.
        
        Args:
            error: Temperature error (target - reference)
            dt: Time delta in seconds since last update
            
        Returns:
            Valve position as integer (0-100)
        """
        if dt <= 0:
            dt = 1.0  # Prevent division by zero

        # Convert dt to minutes for integrator (as per requirements)
        dt_minutes = dt / 60.0

        # Calculate P and I terms
        p_term = self._p_gain * error
        i_term = self._i_gain * self._integrator

        # Desired output (before saturation)
        valve_output_desired = p_term + i_term

        # Apply saturation limits
        valve_output_actual = max(MIN_VALVE_POSITION, min(MAX_VALVE_POSITION, valve_output_desired))

        # Back-calculation anti-windup
        if valve_output_desired != valve_output_actual:
            # We're saturated - calculate excess
            excess = valve_output_desired - valve_output_actual
            # Reduce integrator based on excess (back-calculation)
            self._integrator -= excess * self._anti_windup_gain * dt_minutes
            _LOGGER.debug(
                "Anti-windup active: desired=%f, actual=%f, excess=%f, integrator=%f",
                valve_output_desired, valve_output_actual, excess, self._integrator
            )
        else:
            # Not saturated - normal integration
            self._integrator += error * dt_minutes

        _LOGGER.debug(
            "PI Controller: error=%f, dt=%f, P=%f, I=%f, valve_output=%f, integrator=%f",
            error, dt, p_term, i_term, valve_output_actual, self._integrator
        )

        # Return as integer for clean valve position values
        return round(valve_output_actual)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data and update TRV."""
        # Get current states
        reference_temp = self._get_float_state(self.reference_temp_entity)
        target_temp = self._get_float_state(self.target_temp_entity)
        
        # Get TRV current temperature
        trv_state = self.hass.states.get(self.trv_entity)
        trv_temp = None
        if trv_state and trv_state.attributes.get("current_temperature"):
            try:
                trv_temp = float(trv_state.attributes["current_temperature"])
            except (ValueError, TypeError):
                pass

        # Validate we have all required data
        if reference_temp is None or target_temp is None or trv_temp is None:
            self._startup_attempts += 1
            
            # During startup (first 10 attempts), use debug logging
            # After that, use warning as it might indicate a real problem
            if self._startup_attempts <= 10:
                _LOGGER.debug(
                    "Waiting for entities to initialize (attempt %d): ref=%s, target=%s, trv=%s",
                    self._startup_attempts, reference_temp, target_temp, trv_temp
                )
            else:
                _LOGGER.warning(
                    "Missing required data (attempt %d): ref=%s, target=%s, trv=%s. "
                    "Check that all configured entities exist and are providing values.",
                    self._startup_attempts, reference_temp, target_temp, trv_temp
                )
            
            self.data.update({
                "reference_temp": reference_temp,
                "target_temp": target_temp,
                "trv_temp": trv_temp,
            })
            return self.data

        # Reset startup counter on successful data fetch
        if self._startup_attempts > 0:
            _LOGGER.info(
                "All entities initialized successfully after %d attempts",
                self._startup_attempts
            )
            self._startup_attempts = 0

        # Calculate temperature compensation
        adjusted_target = self._calculate_temperature_compensation(
            target_temp, reference_temp, trv_temp
        )

        # Clamp to safe limits
        adjusted_target = max(MIN_TRV_TARGET_TEMP, min(MAX_TRV_TARGET_TEMP, adjusted_target))

        # Set TRV target temperature
        await self.hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: self.trv_entity,
                ATTR_TEMPERATURE: adjusted_target,
            },
            blocking=True,
        )

        # Calculate error for PI controller
        error = target_temp - reference_temp

        # Update PI controller if we have valve control
        valve_output = 0
        if self.valve_position_entity:
            # Check if TRV is actively heating
            hvac_action = trv_state.attributes.get("hvac_action") if trv_state else None
            
            if hvac_action == "idle":
                # TRV is idle (not heating), set valve to 100% to allow normal operation
                # This ensures TRV can heat properly if HA becomes unavailable
                valve_output = 100
                _LOGGER.debug(
                    "TRV is idle (hvac_action=idle), setting valve to 100%% (allow full heating capability)"
                )
            else:
                # TRV is active, update valve position with PI controller
                now = datetime.now()
                dt = (now - self._last_update).total_seconds() if self._last_update else 1.0
                self._last_update = now

                valve_output = self._update_pi_controller(error, dt)

                # Set valve position
                await self.hass.services.async_call(
                    NUMBER_DOMAIN,
                    SERVICE_SET_VALUE,
                    {
                        ATTR_ENTITY_ID: self.valve_position_entity,
                        "value": valve_output,
                    },
                    blocking=True,
                )
                
                _LOGGER.debug(
                    "Valve position updated: hvac_action=%s, valve=%d%%",
                    hvac_action, valve_output
                )

        # Update stored data
        self.data.update({
            "error": error,
            "integrator": self._integrator,
            "temp_adjustment": adjusted_target - target_temp,
            "valve_output": valve_output,
            "hvac_action": hvac_action,
            "reference_temp": reference_temp,
            "target_temp": target_temp,
            "trv_temp": trv_temp,
        })

        self._last_error = error

        _LOGGER.debug(
            "Updated: ref=%f, target=%f, trv=%f, adjusted=%f, error=%f, valve=%f",
            reference_temp, target_temp, trv_temp, adjusted_target, error, valve_output
        )

        return self.data

    async def _async_update_valve_only(self) -> None:
        """Update only valve position (called periodically)."""
        if not self.valve_position_entity:
            return

        # Get current states
        reference_temp = self._get_float_state(self.reference_temp_entity)
        target_temp = self._get_float_state(self.target_temp_entity)

        if reference_temp is None or target_temp is None:
            return

        # Check if TRV is actively heating
        trv_state = self.hass.states.get(self.trv_entity)
        hvac_action = trv_state.attributes.get("hvac_action") if trv_state else None
        
        if hvac_action == "idle":
            # TRV is idle, set valve to 100% to allow TRV to work independently
            # This is a safety feature - if HA fails, TRV can still heat
            valve_output = 100
            _LOGGER.debug("TRV idle, setting valve to 100%% (failsafe)")
        else:
            # Calculate error
            error = target_temp - reference_temp

            # Update PI controller
            now = datetime.now()
            dt = (now - self._last_update).total_seconds() if self._last_update else 1.0
            self._last_update = now

            valve_output = self._update_pi_controller(error, dt)
            _LOGGER.debug("Valve update: error=%f, valve=%d%%, hvac_action=%s", error, valve_output, hvac_action)

        # Set valve position
        await self.hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: self.valve_position_entity,
                "value": valve_output,
            },
            blocking=False,
        )

        # Update stored data
        self.data.update({
            "error": target_temp - reference_temp if reference_temp else 0,
            "integrator": self._integrator,
            "valve_output": valve_output,
        })

        # Notify listeners
        self.async_set_updated_data(self.data)

