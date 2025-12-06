# TRV Manager for Home Assistant

A sophisticated TRV (Thermostatic Radiator Valve) management integration for Home Assistant that provides:

- **Temperature compensation** to correct TRV readings affected by radiator proximity
- **PI controller** for gradual valve control (prevents full open/close cycling)
- **Per-area management** with external reference sensors

## Features

### Temperature Compensation
TRVs often read higher temperatures than the actual room temperature due to their proximity to the radiator. This integration compensates for this by using an external reference sensor:

```
Adjusted TRV Target = Target Temperature + (TRV Reading - Reference Temperature)
```

Example: If target is 20°C, reference sensor reads 19.7°C, and TRV reads 21°C:
- Adjusted TRV target = 20 + (21 - 19.7) = 21.3°C

### PI Controller with Anti-Windup
When valve position control is available, the integration uses a PI controller to gradually adjust the valve position (0-100%) based on temperature error:

- **Proportional (P) term**: Immediate response to current error
- **Integral (I) term**: Eliminates steady-state error over time
- **Back-calculation anti-windup**: Prevents overshoot when valve saturates
- **Smart idle detection**: Valve control is paused when TRV is idle (not heating)
  - Sets valve limiter to 100% (failsafe: TRV works if HA crashes)
  - Prevents integrator windup
  - Resumes gradual control when heating starts

The controller is tuned so the valve can go from fully closed to fully open (or vice versa) in approximately 20 minutes.

## Installation

1. Copy the `custom_components/trv_manager` directory to your Home Assistant `config/custom_components/` folder
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "TRV Manager"

## Configuration

### Required Entities
- **TRV Climate Entity**: The climate entity representing your TRV
- **Reference Temperature Sensor**: An external temperature sensor in the area
- **Target Temperature Entity**: The desired temperature (can be a sensor, input_number, or number entity)

### Optional Entities
- **Valve Position Entity**: For TRVs that support direct valve position control (0-100%)

### PI Controller Tuning
- **P Gain** (default: 10.0): Controls how aggressively the valve responds to temperature error
  - Higher values = more aggressive response
  - Range: 0-50
  - Units: valve % per degree error
  
- **I Gain** (default: 0.5): Controls how the integrator accumulates error over time
  - Higher values = faster elimination of steady-state error
  - Range: 0-5
  - Units: valve % per degree-minute

### Multiple TRVs in One Area
If you have multiple TRVs in the same area:
1. Create one TRV Manager instance per TRV
2. Use the same reference temperature sensor for all instances
3. Use the same target temperature entity for all instances

This ensures all TRVs work together to heat the area to the target temperature.

## Entities Created

For each TRV Manager instance, the following entities are created:

### Configuration Entities
- **P Gain** (number): Adjust proportional gain
- **I Gain** (number): Adjust integral gain

### Diagnostic Sensors (disabled by default)
- **Temperature Error**: Current error (target - reference)
- **Integrator Value**: Current integrator accumulation
- **Temperature Adjustment**: Temperature compensation applied to TRV
- **Valve Position Output**: PI controller output (0-100%)

Enable diagnostic sensors in the entity settings if you need to monitor or tune the controller.

## How It Works

### Update Behavior
The integration reacts to state changes of:
- Reference temperature sensor
- Target temperature entity
- TRV climate entity

When valve position control is available, it also updates every 60 seconds to refine the PI controller output.

### Safety Limits
- TRV target temperature is clamped to 5-25°C
- Valve position is clamped to 0-100%

### Control Flow

1. **Temperature Compensation** (always active):
   - Reads reference temperature, target temperature, and TRV current temperature
   - Calculates adjusted TRV target using compensation formula
   - Sets TRV target temperature

2. **PI Controller** (when valve position entity is configured):
   - Calculates temperature error (target - reference)
   - Updates PI controller with back-calculation anti-windup
   - **Checks TRV hvac_action**:
     - **If idle**: Sets valve limiter to 100% (failsafe - TRV can work independently if HA crashes)
     - **If heating**: Applies PI output (0-100%) for gradual control

## Tuning Guide

### Starting Point
Use the default gains (P=10.0, I=0.5) and observe the system behavior.

### If temperature oscillates:
- Reduce P gain
- Reduce I gain slightly

### If temperature responds too slowly:
- Increase P gain
- Increase I gain slightly

### If steady-state error persists:
- Increase I gain

### Monitor Diagnostics
Enable the diagnostic sensors to see:
- Error trends
- Integrator behavior
- Valve position changes

## Example Use Case

**Setup:**
- Living room with 2 TRVs on radiators
- 1 external temperature sensor in the center of the room
- 1 schedule helper that changes target temperature throughout the day

**Configuration:**
- Create TRV Manager instance #1 for TRV #1
- Create TRV Manager instance #2 for TRV #2
- Both instances use the same reference sensor and schedule helper
- Both TRVs support valve position control

**Result:**
- Both TRVs compensate for proximity to radiators
- Both TRVs use gradual valve control to maintain comfort
- Room temperature follows the schedule accurately

## Technical Details

### PI Controller Implementation
```python
# P term: immediate response to error
p_term = p_gain * error

# I term: accumulated error over time
i_term = i_gain * integrator

# Desired output
valve_output = p_term + i_term

# Apply saturation (0-100)
valve_output_clamped = clamp(valve_output, 0, 100)

# Back-calculation anti-windup
if valve_output != valve_output_clamped:
    excess = valve_output - valve_output_clamped
    integrator -= excess * kb * dt
else:
    integrator += error * dt
```

### Update Intervals
- State change updates: Immediate
- Valve position updates: Every 60 seconds
- Temperature compensation: On every update

## Troubleshooting

### TRV target temperature not changing
- Check that the TRV entity is correct
- Verify reference and target temperature sensors have valid values
- Check Home Assistant logs for errors

### Valve position not changing
- Ensure valve position entity is configured correctly
- Check that the entity accepts values 0-100
- Verify the entity is not read-only

### Temperature overshoots target
- Reduce P gain
- Check if I gain is too high
- Enable diagnostic sensors to monitor integrator

### Temperature never reaches target
- Increase P gain
- Increase I gain
- Check if TRV valve is functioning properly

## License

This integration is provided as-is for use with Home Assistant.

## Support

For issues, questions, or contributions, please open an issue on the repository.

