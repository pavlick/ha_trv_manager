# Smart Idle Detection Feature

## Overview

The TRV Manager now intelligently detects when the TRV is idle (not heating) and sets the valve position limiter to 100% to ensure the TRV can operate independently if Home Assistant becomes unavailable.

## Understanding Valve Position Control

**Important:** The valve position entity is a **limiter/maximum**, not a direct valve control:

- **100%**: TRV can open valve fully (normal operation)
- **50%**: TRV can only open valve up to 50% (gradual heating)
- **0%**: TRV cannot open valve at all (heating disabled)

The PI controller adjusts this limiter to achieve gradual heating control during active heating periods.

## How It Works

### TRV HVAC Actions

Climate entities in Home Assistant report their current activity through the `hvac_action` attribute:

- **`heating`**: TRV is actively heating (valve open, radiator hot)
- **`idle`**: TRV is closed, not heating (target reached or no heat demand)
- **`off`**: TRV is turned off

### Integration Behavior

#### When TRV is Heating (hvac_action = "heating")
✅ **Active PI control:**
- Temperature compensation applied
- PI controller updates every 60 seconds
- Valve limiter adjusted based on temperature error (0-100%)
- Gradual heating control to prevent overshooting

#### When TRV is Idle (hvac_action = "idle")
🔵 **Failsafe mode:**
- Temperature compensation still applied to TRV target
- **Valve limiter set to 100%** (TRV can heat fully if needed)
- **PI controller updates paused** (integrator frozen)
- **Safety feature**: If HA dies, TRV can still heat normally

#### When TRV State Unknown
⚠️ **Cautious operation:**
- Assumes heating (safer to control than to ignore)
- Normal PI controller operation

## Benefits

### 1. Resilience / Failsafe
✅ **Most important**: If Home Assistant crashes or becomes unavailable:
- TRV can still operate independently
- Valve is not artificially limited
- Room can still be heated
- No "stuck at low temperature" scenario

### 2. Energy Efficiency
- No valve limiter adjustments when not heating
- Prevents unnecessary service calls
- Reduces log noise

### 3. Better Control
- Prevents integrator from growing when TRV is closed
- Cleaner transitions when heating resumes
- PI controller only active when it matters

### 4. Logical Behavior
- Idle = "get out of the way, let TRV work"
- Heating = "assist with gradual control"
- Matches design intent of valve position as a limiter

## Example Scenarios

### Scenario 1: Target Reached
```
Time  | Ref Temp | Target | Error | hvac_action | Valve Limiter | Behavior
------|----------|--------|-------|-------------|---------------|----------
10:00 | 19.5°C   | 20.0°C | +0.5  | heating     | 45%           | ✅ Gradual heating
10:15 | 19.9°C   | 20.0°C | +0.1  | heating     | 12%           | ✅ Nearly there
10:30 | 20.1°C   | 20.0°C | -0.1  | idle        | 100%          | 🔵 Idle, failsafe active
10:45 | 20.1°C   | 20.0°C | -0.1  | idle        | 100%          | 🔵 Still idle, TRV free
11:00 | 19.8°C   | 20.0°C | +0.2  | heating     | 15%           | ✅ Resumed gradual control
```

**Key insight**: When idle, valve limiter at 100% means "TRV, you're in control, do what you need"

### Scenario 2: Home Assistant Crash During Idle
```
Time  | Event                        | Valve Limiter | TRV Behavior
------|------------------------------|---------------|-------------
14:00 | Room at target, TRV idle     | 100%          | ✅ TRV closed, comfortable
14:15 | HA crashes! 💥               | 100% (last)   | ✅ TRV still works!
14:30 | Room cools, TRV wants heat   | 100% (stuck)  | ✅ TRV can heat fully
15:00 | Room reaches target again    | 100% (stuck)  | ✅ TRV closes normally
15:30 | HA restored                  | 100% → PI     | ✅ Gradual control resumes
```

**Without failsafe (valve at 0%)**: TRV would be unable to heat, room would get cold! ❌

### Scenario 3: Home Assistant Crash During Heating
```
Time  | Event                        | Valve Limiter | TRV Behavior
------|------------------------------|---------------|-------------
16:00 | Room cold, actively heating  | 65%           | ✅ Gradual heating active
16:15 | HA crashes! 💥               | 65% (stuck)   | ⚠️ TRV limited to 65%
16:30 | TRV continues heating        | 65% (stuck)   | ⚠️ Slower heating
17:00 | Room reaches target          | 65% (stuck)   | ✅ TRV closes
17:05 | Room drops slightly          | 65% (stuck)   | ✅ TRV can still heat
18:00 | HA restored                  | 65% → 100%    | ✅ Control resumes
```

**Note**: Even if stuck at 65%, TRV can still heat (just not at 100% power). Not ideal, but room stays warm.

## Technical Details

### Idle Detection Logic

```python
# Check TRV hvac_action
hvac_action = trv_state.attributes.get("hvac_action")

if hvac_action == "idle":
    # TRV is not heating - set limiter to 100%
    # This is a FAILSAFE: if HA dies, TRV can still work
    valve_output = 100
    # Skip PI controller update (integrator frozen)
else:
    # TRV is heating or state unknown
    valve_output = pi_controller.update(error, dt)
    # Normal gradual control (0-100%)
```

### What the Valve Position Actually Controls

The valve position entity is **NOT** the actual valve state. It's a **limiter**:

```
TRV decides to open valve to 80%
├─ Integration valve limiter: 100% → TRV opens to 80% ✅
├─ Integration valve limiter: 50%  → TRV limited to 50% ⚠️
└─ Integration valve limiter: 0%   → TRV cannot open ❌

TRV decides to close valve (idle)
├─ Integration valve limiter: 100% → TRV closed, but can reopen ✅
├─ Integration valve limiter: 50%  → TRV closed, limited if reopens ⚠️
└─ Integration valve limiter: 0%   → TRV closed, cannot reopen ❌
```

**Key insight**: The limiter only matters when TRV wants to heat. When idle, 100% ensures TRV freedom.

## Logs

### When TRV Goes Idle

```
DEBUG: TRV is idle (hvac_action=idle), setting valve to 100% (allow full heating capability)
DEBUG: Updated: ref=20.1, target=20.0, trv=20.2, adjusted=20.1, error=-0.1, valve=100
```

### When TRV Resumes Heating

```
DEBUG: Valve position updated: hvac_action=heating, valve=15%
DEBUG: PI Controller: error=0.2, dt=60.0, P=2.0, I=13.5, valve_output=15, integrator=27.0
```

### Periodic Updates While Idle

```
DEBUG: TRV idle, setting valve to 100% (failsafe)
```

## Dashboard Integration

You can see when the TRV is idle by:

1. **Checking the TRV entity:**
   - View `climate.your_trv` in Developer Tools → States
   - Look at `hvac_action` attribute

2. **Monitoring valve limiter:**
   - Enable diagnostic sensor: `sensor.your_name_valve_output`
   - Should show 100% when idle (failsafe active)
   - Shows PI output (0-100%) when heating

3. **History Graph:**
   ```yaml
   type: history-graph
   entities:
     - sensor.room_temperature
     - input_number.target_temp
     - sensor.your_name_valve_output
     - climate.your_trv  # Shows hvac_action in tooltip
   ```

## Compatibility

This feature works with any TRV that:
- ✅ Reports `hvac_action` attribute
- ✅ Uses standard values: "heating", "idle", "off"

Most modern TRVs support this:
- Zigbee TRVs (via Zigbee2MQTT, ZHA)
- Z-Wave TRVs
- Native integrations (tado, Shelly, etc.)

If your TRV doesn't report `hvac_action`:
- Integration will assume heating (safe default)
- Normal operation continues
- No errors or warnings

## Configuration

**No configuration needed!** This feature is automatic when:
1. You have configured a valve position entity
2. Your TRV reports `hvac_action`

The integration will automatically:
- ✅ Detect when TRV is idle
- ✅ Pause valve control
- ✅ Resume when heating starts

## Disabling (If Needed)

If you want valve control even when idle (not recommended), you would need to:
1. Remove this check from the code
2. Restart Home Assistant

**However, there's no good reason to do this** - controlling a closed valve makes no sense.

## Summary

Smart idle detection with failsafe:
- ✅ **Failsafe protection**: TRV works even if HA dies
- ✅ **Valve limiter to 100% when idle**: TRV has full control
- ✅ **Gradual control when heating**: PI controller prevents overshooting
- ✅ Prevents integrator windup during idle
- ✅ Automatic, no configuration needed
- ✅ No impact if TRV doesn't report hvac_action

**Most important benefit**: If Home Assistant crashes, your TRVs can still heat your home! This is a critical safety and reliability feature. 🎉

