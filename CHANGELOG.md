# Changelog

## [0.1.0] - 2024-12-05

### Initial Release

#### Features
- Temperature compensation for TRVs affected by radiator proximity
- PI controller with back-calculation anti-windup for gradual valve control
- UI-based configuration (Config Flow)
- Runtime tunable P and I gains via number entities
- Diagnostic sensors for monitoring (disabled by default)
- Support for multiple TRVs in same area
- Automatic updates on state changes
- Periodic valve updates (60 seconds)
- Safety limits (TRV: 5-25°C, Valve: 0-100%)

#### Core Components
- `coordinator.py`: Main control logic with PI controller
- `config_flow.py`: UI configuration wizard
- `number.py`: P/I gain control entities
- `sensor.py`: Diagnostic sensors
- `const.py`: Constants and configuration
- `__init__.py`: Integration lifecycle management

#### Documentation
- README.md: Complete user guide
- QUICK_START.md: Quick reference and getting started
- TROUBLESHOOTING.md: Detailed troubleshooting guide
- EXAMPLE_CONFIG.yaml: Configuration examples
- IMPLEMENTATION_SUMMARY.md: Technical architecture

### Fixed (before release)
- **Idle failsafe**: Valve limiter set to 100% when TRV idle (was 0%) - ensures TRV can work independently if HA crashes  
- **Idle detection**: Valve control now paused when TRV is idle (hvac_action='idle'), prevents integrator windup
- **Valve position precision**: Valve position now rounded to integer (0-100) instead of float with many decimals
- **Startup logging**: Improved logging during startup - uses DEBUG level for first 10 initialization attempts, reducing log noise
- **Options flow error**: Removed `__init__` from `TRVManagerOptionsFlow` - parent class already provides `config_entry` property
- **Import error**: Fixed `SERVICE_SET_TEMPERATURE` import - now correctly imported from `homeassistant.components.climate` instead of `homeassistant.const`
- **Config flow compatibility**: Changed from `EntitySelectorConfig()` to dict-based selectors for better compatibility
- **Integration type**: Changed from `"device"` to `"hub"` in manifest.json
- **Import optimization**: Removed unused imports from config_flow.py to prevent blocking call warnings
- **Selector syntax**: Simplified entity selector configuration for Home Assistant compatibility

### Technical Details

#### Temperature Compensation Algorithm
```python
adjusted_target = target_temp + (trv_temp - reference_temp)
adjusted_target = clamp(adjusted_target, 5, 25)
```

#### PI Controller with Anti-Windup
```python
p_term = p_gain * error
i_term = i_gain * integrator
valve_output = p_term + i_term

# Back-calculation anti-windup
if saturated:
    integrator -= excess * kb * dt
else:
    integrator += error * dt
```

#### Default Parameters
- P Gain: 10.0 (valve % per degree error)
- I Gain: 0.5 (valve % per degree-minute)
- Anti-windup Gain: 1.0
- Valve Update Interval: 60 seconds
- TRV Target Range: 5-25°C
- Valve Position Range: 0-100%

### Known Limitations
- Integrator resets on Home Assistant restart (by design)
- Requires valid entity states to operate
- One reference sensor per instance
- Manual TRV control should be avoided (use target temperature entity instead)

### Compatibility
- Home Assistant: 2023.8+
- Python: 3.11+
- No external dependencies

### Future Enhancements (Potential)
- Integrator persistence across restarts
- Adaptive gain tuning
- Multi-sensor averaging
- Dead band implementation
- Occupancy-based adjustments
- Derivative term (PID)
- Weather-based preheating

---

## Version History

### [0.1.0] - 2024-12-05
- Initial release with temperature compensation and PI control
- Config flow implementation
- Diagnostic sensors
- Runtime tunable gains
- Complete documentation

