"""Constants for the TRV Manager integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "trv_manager"

# Configuration keys
CONF_TRV_ENTITY: Final = "trv_entity"
CONF_REFERENCE_TEMP_ENTITY: Final = "reference_temp_entity"
CONF_TARGET_TEMP_ENTITY: Final = "target_temp_entity"
CONF_VALVE_POSITION_ENTITY: Final = "valve_position_entity"
CONF_P_GAIN: Final = "p_gain"
CONF_I_GAIN: Final = "i_gain"
CONF_ANTI_WINDUP_GAIN: Final = "anti_windup_gain"

# Default values
DEFAULT_P_GAIN: Final = 10.0  # Proportional gain (valve % per degree error)
DEFAULT_I_GAIN: Final = 0.5   # Integral gain (valve % per degree-minute)
DEFAULT_ANTI_WINDUP_GAIN: Final = 1.0  # Back-calculation gain

# Limits
MIN_TRV_TARGET_TEMP: Final = 5.0  # °C
MAX_TRV_TARGET_TEMP: Final = 25.0  # °C
MIN_VALVE_POSITION: Final = 0.0
MAX_VALVE_POSITION: Final = 100.0

# Update intervals
VALVE_UPDATE_INTERVAL: Final = timedelta(seconds=60)
FAST_UPDATE_INTERVAL: Final = timedelta(seconds=5)

# PI controller limits
MIN_P_GAIN: Final = 0.0
MAX_P_GAIN: Final = 50.0
MIN_I_GAIN: Final = 0.0
MAX_I_GAIN: Final = 5.0

# Entity suffixes
ENTITY_ID_P_GAIN: Final = "_p_gain"
ENTITY_ID_I_GAIN: Final = "_i_gain"
ENTITY_ID_ERROR: Final = "_error"
ENTITY_ID_INTEGRATOR: Final = "_integrator"
ENTITY_ID_TEMP_ADJUSTMENT: Final = "_temp_adjustment"
ENTITY_ID_VALVE_OUTPUT: Final = "_valve_output"

