# TRV Manager Hub Architecture - Implementation Summary

## Overview
The TRV Manager integration has been restructured from a single-device model to a **hub + multiple devices** architecture. This allows you to create one hub per area (e.g., "Living Room Hub") and manage multiple TRV devices under it, all sharing the same reference temperature and target temperature entities.

## Architecture Changes

### Before (v0.2.0)
- **One Config Entry** = **One Device**
- Each entry required its own reference temp and target temp entities
- Managing multiple TRVs in the same area required duplicate configuration

### After (v0.3.0)
- **One Config Entry (Hub)** = **Multiple Devices**
- Hub stores: Reference temp entity, Target temp entity (shared by all devices)
- Each device stores: TRV entity, Valve position entity, P/I gains (independent)
- Each device gets its own coordinator instance with independent PI controller state

## Key Benefits

1. **Logical Grouping**: All TRVs in one area are grouped under one hub
2. **Shared Configuration**: One reference sensor and target temperature for the whole area
3. **Independent Control**: Each TRV maintains its own PI controller state and settings
4. **Easier Management**: Add/remove TRVs through the options menu
5. **Better UI Organization**: Clear parent-child relationship in device registry

## File Changes

### 1. `const.py`
- Separated configuration keys into hub-level and device-level
- Added `CONF_DEVICES`, `CONF_DEVICE_ID`, `CONF_DEVICE_NAME`

### 2. `config_flow.py`
- **Version bumped to 2** for new structure
- Multi-step config flow:
  1. Create hub (name, reference temp, target temp)
  2. Add first device (device name, TRV entity, optional settings)
  3. Option to add more devices
- Options flow with menu system:
  - Configure hub settings (update shared sensors)
  - Manage devices (add/edit/remove devices)

### 3. `__init__.py`
- Creates hub device in device registry
- Creates one coordinator per device
- Each device linked to hub via `via_device`
- Stores data structure:
  ```python
  hass.data[DOMAIN][entry.entry_id] = {
      "hub_name": "Living Room Hub",
      "reference_temp_entity": "sensor.room_temp",
      "target_temp_entity": "input_number.room_target",
      "coordinators": {
          "device_id_1": {
              "coordinator": coordinator1,
              "device_name": "Radiator 1",
              "trv_entity": "climate.rad1",
          },
          "device_id_2": {...},
      }
  }
  ```

### 4. `coordinator.py`
- Updated constructor to accept `device_id` parameter
- All existing logic remains unchanged (temperature compensation, PI controller, valve control)
- Each coordinator operates independently

### 5. `number.py` and `sensor.py`
- Updated to create entities for each device
- Device info includes `via_device` to link to hub
- Unique IDs now include both entry_id and device_id

### 6. `manifest.json`
- Version updated to 0.3.0
- Already marked as `integration_type: "hub"`

### 7. `strings.json` and `translations/en.json`
- Updated for new multi-step config flow
- Added strings for hub and device management

## Device Registry Structure

```
Hub Device
├─ identifiers: {(DOMAIN, entry.entry_id)}
├─ name: "Living Room Hub"
├─ manufacturer: "TRV Manager"
└─ model: "Hub"

Device 1
├─ identifiers: {(DOMAIN, f"{entry.entry_id}_{device_id_1}")}
├─ name: "Radiator 1"
├─ manufacturer: "TRV Manager"
├─ model: "TRV Controller"
├─ via_device: (DOMAIN, entry.entry_id)  # Links to hub
└─ Entities:
    ├─ P Gain (number)
    ├─ I Gain (number)
    ├─ Temperature Error (sensor)
    ├─ Integrator Value (sensor)
    ├─ Temperature Adjustment (sensor)
    └─ Valve Position Output (sensor)

Device 2
├─ identifiers: {(DOMAIN, f"{entry.entry_id}_{device_id_2}")}
├─ ...
```

## User Workflow

### Creating a New Hub

1. **Add Integration**: Navigate to Settings → Devices & Services → Add Integration → TRV Manager
2. **Create Hub**: 
   - Enter hub name (e.g., "Living Room")
   - Select reference temperature sensor
   - Select target temperature entity
3. **Add First Device**:
   - Enter device name (e.g., "Radiator 1")
   - Select TRV climate entity
   - Optionally configure valve position entity and PI gains
4. **Add More Devices** (optional):
   - Choose "Yes" to add another device
   - Repeat step 3
5. **Done**: Click "Submit" when finished adding devices

### Managing Devices

1. **Open Options**: Click "Configure" on the TRV Manager hub
2. **Choose Action**:
   - **Configure Hub Settings**: Update shared reference/target temp entities
   - **Manage Devices**: Add/Edit/Remove individual TRV devices

## Migration Notes

**No automatic migration** is provided from v0.2.0 to v0.3.0. Users will need to:
1. Remove old TRV Manager entries (one per TRV)
2. Create new hub(s) with the new structure
3. Add TRV devices to appropriate hubs

This is intentional because:
- Difficult to determine which old entries should be merged into which hubs
- Cleaner to start fresh with the new logical structure
- Gives users control over hub organization

## Testing

All Python files have been validated for syntax errors and compile successfully. JSON configuration files are valid.

## Backward Compatibility

The config flow version has been bumped from 1 to 2, indicating a breaking change. Existing installations will continue to work but won't benefit from the new structure until reconfigured.

## Technical Details

- Each device maintains its own PI controller state (integrator, last updates, etc.)
- Coordinators operate independently and don't interfere with each other
- All devices in a hub share the same reference and target temperature readings
- Entity unique IDs are globally unique: `{entry_id}_{device_id}_{entity_type}`
- Device IDs are generated using `uuid.uuid4()` for uniqueness

## Example Use Case

**Scenario**: Living room with 3 radiators, each with a TRV

**Before (v0.2.0)**:
- Create 3 separate TRV Manager entries
- Configure same reference sensor 3 times
- Configure same target temperature 3 times

**After (v0.3.0)**:
- Create 1 hub: "Living Room Hub"
- Add 3 devices: "Radiator 1", "Radiator 2", "Radiator 3"
- All share one reference sensor and one target temperature
- Each maintains independent PI control

---

**Version**: 0.3.0  
**Config Flow Version**: 2  
**Date**: December 7, 2024
