# TRV Manager - Quick Start Guide

## What You Need to Fix the Error

The "Invalid handler specified" error has been fixed by:
1. ✅ Simplified selector configuration (using dict instead of SelectorConfig)
2. ✅ Changed integration_type from "device" to "hub" in manifest.json
3. ✅ Removed unused imports from config_flow.py

## Next Steps

### 1. Restart Home Assistant
**Important:** You MUST restart Home Assistant after making changes to custom integrations.

- Option A: Settings → System → Restart
- Option B: Developer Tools → YAML → Restart
- Option C: If running in Docker: `docker restart homeassistant`

### 2. Clear Browser Cache
After restart, clear your browser cache:
- **Chrome/Edge**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- **Firefox**: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
- **Safari**: Cmd+Option+R

### 3. Add the Integration
1. Go to Settings → Devices & Services
2. Click "+ ADD INTEGRATION" (bottom right)
3. Search for "TRV Manager"
4. Fill in the form:
   - **Name**: Give it a descriptive name (e.g., "Living Room TRV 1")
   - **TRV Climate Entity**: Select your TRV (must be a climate entity)
   - **Reference Temperature Sensor**: Select an external thermometer
   - **Target Temperature Entity**: Select your target temp (sensor, input_number, or number)
   - **Valve Position Entity** (optional): If your TRV supports direct valve control
   - **P Gain**: Leave at default (10.0) initially
   - **I Gain**: Leave at default (0.5) initially

## What the Integration Does

### Always Active: Temperature Compensation
Your TRV reads higher than actual room temperature because it's close to the hot radiator.
The integration fixes this automatically:

```
If target is 20°C, room is 19.7°C, but TRV reads 21°C:
→ Integration sets TRV target to 21.3°C
→ This makes the room reach the actual 20°C target
```

### When Valve Control Available: PI Controller
Prevents valve from swinging fully open/closed, provides gradual control:

```
Cold room → Slowly opens valve as needed
Approaching target → Gradually reduces valve opening
At target → Maintains small valve opening
```

## Entities Created

For each instance, you get:

### Configuration Entities (always visible)
- `number.NAME_p_gain` - Adjust P gain (tuning)
- `number.NAME_i_gain` - Adjust I gain (tuning)

### Diagnostic Sensors (disabled by default, enable if needed)
- `sensor.NAME_error` - Temperature error (target - actual)
- `sensor.NAME_integrator` - Internal PI controller state
- `sensor.NAME_temp_adjustment` - Compensation applied to TRV
- `sensor.NAME_valve_output` - Valve position output (0-100%)

## Multiple TRVs in Same Room

If you have 2 TRVs in the living room:

**Instance 1:**
- Name: Living Room TRV 1
- TRV Entity: `climate.living_room_trv_1`
- Reference Sensor: `sensor.living_room_temperature` ← SAME
- Target Temperature: `input_number.living_room_target` ← SAME
- Valve Entity: `number.living_room_trv_1_position`

**Instance 2:**
- Name: Living Room TRV 2
- TRV Entity: `climate.living_room_trv_2`
- Reference Sensor: `sensor.living_room_temperature` ← SAME
- Target Temperature: `input_number.living_room_target` ← SAME
- Valve Entity: `number.living_room_trv_2_position`

Both instances work together to heat the room to the target temperature.

## Tuning the PI Controller

### Start with Defaults
- P Gain: 10.0
- I Gain: 0.5

### Observe the Behavior
Monitor room temperature for a few hours:

**Problem: Temperature oscillates (goes up and down)**
- Solution: Reduce P gain (try 8.0, then 6.0)
- If still oscillating: Reduce I gain slightly (try 0.3)

**Problem: Takes too long to reach target**
- Solution: Increase P gain (try 12.0, then 15.0)
- If steady-state error persists: Increase I gain (try 0.7)

**Problem: Temperature reaches target but stays slightly off**
- Solution: Increase I gain (try 0.7, then 1.0)

### Monitor Diagnostics
Enable diagnostic sensors to see what's happening:
1. Go to Settings → Devices & Services → TRV Manager
2. Click on a diagnostic sensor
3. Click the gear icon
4. Enable the entity
5. View in Developer Tools → States or add to dashboard

## Troubleshooting

### Integration doesn't appear
- Restart Home Assistant
- Clear browser cache
- Check logs: Settings → System → Logs

### Config flow shows error
- Verify you have climate entities available
- Verify you have temperature sensors
- Check TROUBLESHOOTING.md for detailed steps

### TRV not responding
- Check TRV entity is correct
- Verify TRV accepts temperature commands
- Look for errors in Home Assistant logs

### Valve position not working
- Verify valve entity accepts values 0-100
- Check entity is not read-only
- Ensure entity is type `number` or `input_number`

## Getting Started Example

1. **Create target temperature helper:**
   - Settings → Devices & Services → Helpers
   - Add Helper → Number
   - Name: "Living Room Target Temperature"
   - Min: 15, Max: 25, Step: 0.5
   - Unit: °C

2. **Add TRV Manager integration:**
   - Settings → Devices & Services → Add Integration
   - Search: "TRV Manager"
   - Fill in form with your entities

3. **Test it:**
   - Change the target temperature helper
   - Watch the TRV adjust
   - Monitor room temperature

4. **Create automation (optional):**
   - Automate target temperature based on schedule
   - See EXAMPLE_CONFIG.yaml for examples

## Support Files

- **README.md**: Complete documentation
- **EXAMPLE_CONFIG.yaml**: Configuration examples
- **TROUBLESHOOTING.md**: Detailed troubleshooting
- **IMPLEMENTATION_SUMMARY.md**: Technical details

## Changes Made to Fix the Error

The following files were updated:

1. **config_flow.py**:
   - Changed from `EntitySelectorConfig(domain="climate")` to `{"domain": "climate"}`
   - Removed unused imports (HomeAssistant, async_get_entity_registry)

2. **manifest.json**:
   - Changed `integration_type` from `"device"` to `"hub"`

3. **coordinator.py**:
   - Fixed import: `SERVICE_SET_TEMPERATURE` now imported from `homeassistant.components.climate` instead of `homeassistant.const`

These changes ensure compatibility with your Home Assistant version.

---

**Now restart Home Assistant and try adding the integration again!**

