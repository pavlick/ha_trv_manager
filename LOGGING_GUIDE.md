# Logging and Diagnostics Guide

## Log Levels

The TRV Manager integration uses different log levels for different situations:

### DEBUG Level
- Normal operational updates
- Entity state changes
- PI controller calculations
- Temperature adjustments
- Startup initialization (first 10 attempts)

### INFO Level
- Integration initialization
- Successful entity loading after startup
- Configuration changes

### WARNING Level
- Missing entity data after startup (11+ failed attempts)
- Invalid state conversions
- Unexpected errors during operation

## Understanding Startup Behavior

### Normal Startup Sequence

When Home Assistant starts or the integration is added, you may see debug messages like:
```
Waiting for entities to initialize (attempt 1): ref=None, target=25.0, trv=None
Waiting for entities to initialize (attempt 2): ref=None, target=25.0, trv=19.4
Waiting for entities to initialize (attempt 3): ref=19.3, target=25.0, trv=None
All entities initialized successfully after 3 attempts
```

This is **completely normal** - entities initialize at different times during startup.

### When to Be Concerned

If you see warning messages like:
```
Missing required data (attempt 15): ref=None, target=25.0, trv=None.
Check that all configured entities exist and are providing values.
```

This indicates a potential problem:
- Entity doesn't exist
- Entity is unavailable
- Entity is not providing temperature data
- Wrong entity selected in configuration

## Enabling Debug Logging

To see detailed operation logs, enable debug logging for the integration:

### Method 1: configuration.yaml (Persistent)

Add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.trv_manager: debug
    custom_components.trv_manager.coordinator: debug
```

Then restart Home Assistant.

### Method 2: Service Call (Temporary - until restart)

1. Go to Developer Tools → Services
2. Call service: `logger.set_level`
3. Service data:
```yaml
custom_components.trv_manager: debug
```

## What You'll See in Logs

### During Normal Operation (DEBUG)

```
[custom_components.trv_manager.coordinator] Updated: ref=19.3, target=20.0, trv=20.1, adjusted=20.8, error=0.7, valve=15.3
```

This shows:
- **ref**: Reference temperature (actual room temp)
- **target**: Target temperature (setpoint)
- **trv**: TRV's current temperature reading
- **adjusted**: Adjusted target sent to TRV (includes compensation)
- **error**: Temperature error (target - reference)
- **valve**: Valve position output from PI controller

### Temperature Compensation

```
[custom_components.trv_manager.coordinator] Temperature compensation: target=20.0, ref=19.3, trv=20.1, compensation=0.8, adjusted=20.8
```

Shows the compensation calculation:
- TRV reads 20.1°C but room is actually 19.3°C
- Difference (compensation) = 0.8°C
- Adjusted TRV target = 20.0 + 0.8 = 20.8°C

### PI Controller

```
[custom_components.trv_manager.coordinator] PI Controller: error=0.7, dt=60.0, P=7.0, I=2.1, valve_output=15.3, integrator=4.2
```

Shows:
- **error**: Current temperature error
- **dt**: Time since last update (seconds)
- **P**: Proportional term contribution
- **I**: Integral term contribution
- **valve_output**: Final output (0-100%)
- **integrator**: Current integrator state

### Anti-Windup Active

```
[custom_components.trv_manager.coordinator] Anti-windup active: desired=105.3, actual=100.0, excess=5.3, integrator=18.7
```

Shows when the output saturates (hits 100% or 0%) and anti-windup kicks in:
- **desired**: What the controller wanted to output
- **actual**: Clamped output (100% max)
- **excess**: How much over the limit
- **integrator**: Integrator value after back-calculation

## Viewing Logs

### Home Assistant UI
1. Settings → System → Logs
2. Filter by "trv_manager" to see only relevant logs
3. Refresh to see latest logs

### Log File
Logs are in: `/config/home-assistant.log`

You can tail the log file:
```bash
tail -f /config/home-assistant.log | grep trv_manager
```

Or in Docker:
```bash
docker logs -f homeassistant | grep trv_manager
```

## Common Log Messages Explained

### "Waiting for entities to initialize"
**Normal during startup** - entities are still loading. No action needed.

### "All entities initialized successfully"
**Good news** - integration is fully operational.

### "Missing required data (attempt 15+)"
**Problem** - Check your configuration:
- Verify entity IDs are correct
- Check entities are available (not "unavailable" or "unknown")
- Ensure TRV provides `current_temperature` attribute

### "Could not convert state of X to float"
**Issue** - Entity is providing non-numeric value:
- Check the entity's state in Developer Tools → States
- Verify it's a temperature sensor with numeric values
- Check entity is not in error state

### "Anti-windup active"
**Normal operation** - Valve is at max/min, PI controller is handling saturation properly.

### "Updated: ref=X, target=Y..."
**Normal debug output** - Shows the integration is working and updating values.

## Performance Monitoring

### What to Monitor

1. **Update frequency**: Should see updates when states change + every 60s for valve
2. **Error values**: Should trend toward 0 over time
3. **Valve output**: Should adjust smoothly, not jump
4. **Integrator**: Should stay reasonable (not growing unbounded)

### Healthy Operation Indicators

- ✅ Error within ±0.5°C most of the time
- ✅ Smooth valve position changes (if valve control enabled)
- ✅ No repeated warnings about missing data
- ✅ Temperature adjustment stays relatively stable
- ✅ Integrator stays in reasonable range (-50 to +50)

### Potential Issues

- ⚠️ Error consistently >1°C → System can't keep up or TRV issue
- ⚠️ Valve jumping 0% ↔ 100% → Gains need tuning
- ⚠️ Integrator growing unbounded → Check anti-windup, adjust gains
- ⚠️ Repeated missing data warnings → Entity configuration issue

## Diagnostic Sensors vs. Logs

### Diagnostic Sensors (Recommended for Users)
- Real-time values visible in dashboard
- Easy to monitor trends over time
- History graphs available
- No need to dig through logs

### Debug Logs (For Troubleshooting)
- Detailed operational information
- Useful for understanding behavior
- Needed for debugging issues
- Better for developers/advanced users

**Recommendation**: Enable diagnostic sensors for daily monitoring, use debug logs only when troubleshooting issues.

## Example: Troubleshooting with Logs

### Scenario: Room not reaching target temperature

1. **Enable debug logging**
2. **Watch logs for 5-10 minutes**
3. **Look for**:
   - What is the error value?
   - Is valve reaching 100%?
   - Is temperature adjustment correct?
   - Is integrator growing?

4. **Interpret**:
   - Error large + valve at 100% = Not enough heating capacity
   - Error large + valve at 50% = Gains too low, increase P
   - Valve oscillating = Gains too high, reduce P
   - Steady-state error = Increase I gain

5. **Adjust and monitor** changes in logs

## Getting Help

When asking for help, include:
1. Relevant log excerpts (with debug enabled)
2. Current configuration (P/I gains)
3. Entity states from Developer Tools → States
4. Description of the problem
5. What you've tried so far

This helps diagnose issues much faster than descriptions alone.

