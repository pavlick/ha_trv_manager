# Multi-TRV Design: Architecture Comparison

> **TL;DR**: Your multi-TRV idea is good and feasible, but the current single-TRV design is already production-ready. Ship it now, add multi-TRV later if users want it.

---

## Your Proposed Design (Multi-TRV per Area)

### User Experience

**Configuration Flow:**
```
Step 1: Area Setup
├─ Area Name: "Living Room"
├─ Reference Sensor: sensor.living_room_temp
└─ Target Temperature: input_number.living_room_target

Step 2: Add TRV (repeated)
├─ [Add TRV Button]
│
├─ TRV 1:
│   ├─ Climate Entity: climate.living_room_trv_1
│   ├─ Valve Entity: number.valve_1
│   ├─ P Gain: 8.0
│   ├─ I Gain: 0.3
│   └─ Name: "Big Radiator"
│
├─ TRV 2:
│   ├─ Climate Entity: climate.living_room_trv_2
│   ├─ Valve Entity: number.valve_2
│   ├─ P Gain: 12.0
│   ├─ I Gain: 0.7
│   └─ Name: "Small Radiator"
│
└─ [Finish]

Result: ONE integration instance for the whole area
```

**Entities Created:**
```
Device: TRV Manager - Living Room
├─ number.living_room_big_radiator_p_gain
├─ number.living_room_big_radiator_i_gain
├─ number.living_room_small_radiator_p_gain
├─ number.living_room_small_radiator_i_gain
├─ sensor.living_room_error (diagnostic)
├─ sensor.living_room_big_radiator_valve_output (diagnostic)
├─ sensor.living_room_big_radiator_integrator (diagnostic)
├─ sensor.living_room_small_radiator_valve_output (diagnostic)
└─ sensor.living_room_small_radiator_integrator (diagnostic)
```

### Advantages ✅

1. **Better UX**:
   - Single configuration per area
   - No duplicate reference/target configuration
   - Organized by logical groups
   - Easy to see all TRVs in one area

2. **Cleaner HA UI**:
   - One device per area
   - All controls grouped together
   - Fewer integration instances

3. **Easier Management**:
   - Change reference sensor once (affects all TRVs)
   - Change target once (affects all TRVs)
   - Add/remove TRVs from area easily

4. **Better Organization**:
   - Natural grouping by room/area
   - Reflects physical reality
   - Easier for users to understand

### Disadvantages ❌

1. **More Complex Implementation**:
   - Multi-step config flow
   - Need to manage list of TRV configs
   - More complex data structure
   - Options flow needs custom UI for editing list

2. **Harder to Migrate**:
   - Can't easily migrate from current version
   - Users would need to reconfigure

3. **Options Flow Complexity**:
   - Need UI to add/remove/edit individual TRVs
   - Can't use simple form (need multi-step)

## Current Design (One Instance per TRV)

### User Experience

**Configuration Flow:**
```
Instance 1:
├─ Name: "Living Room - Big Radiator"
├─ TRV: climate.living_room_trv_1
├─ Reference: sensor.living_room_temp
├─ Target: input_number.living_room_target
├─ Valve: number.valve_1
├─ P Gain: 8.0
└─ I Gain: 0.3

Instance 2:
├─ Name: "Living Room - Small Radiator"  
├─ TRV: climate.living_room_trv_2
├─ Reference: sensor.living_room_temp (duplicate)
├─ Target: input_number.living_room_target (duplicate)
├─ Valve: number.valve_2
├─ P Gain: 12.0
└─ I Gain: 0.7

Result: TWO integration instances
```

**Entities Created:**
```
Device 1: Living Room - Big Radiator
├─ number.living_room_big_radiator_p_gain
├─ number.living_room_big_radiator_i_gain
├─ sensor.living_room_big_radiator_error (diagnostic)
└─ sensor.living_room_big_radiator_valve_output (diagnostic)

Device 2: Living Room - Small Radiator
├─ number.living_room_small_radiator_p_gain
├─ number.living_room_small_radiator_i_gain
├─ sensor.living_room_small_radiator_error (diagnostic)
└─ sensor.living_room_small_radiator_valve_output (diagnostic)
```

### Advantages ✅

1. **Simpler Implementation**:
   - Simple single-step config flow ✅ (already done!)
   - Standard HA patterns
   - Easier to maintain
   - Simple options flow

2. **Independent Control**:
   - Each TRV completely independent
   - Can reload one without affecting others
   - Easy to disable/enable individual TRVs

3. **Easier Migration**:
   - Already implemented ✅
   - Users already configuring it
   - No breaking changes needed

4. **Flexibility**:
   - Can use different reference sensors if needed
   - Can have different targets (rare but possible)
   - Each TRV is a separate "device"

### Disadvantages ❌

1. **Duplicate Configuration**:
   - Must enter reference/target for each TRV
   - More clicking during setup
   - If reference sensor changes, update multiple instances

2. **More Instances**:
   - Living room with 3 TRVs = 3 instances
   - Can clutter integrations page

3. **Less Organized**:
   - TRVs not visually grouped by area
   - User needs to use naming convention

## Technical Architecture Comparison

### Data Storage

**Multi-TRV Approach:**
```python
{
    "name": "Living Room",
    "reference_temp_entity": "sensor.living_room_temp",
    "target_temp_entity": "input_number.living_room_target",
    "trvs": [
        {
            "trv_entity": "climate.trv_1",
            "valve_entity": "number.valve_1",
            "p_gain": 8.0,
            "i_gain": 0.3,
            "name": "Big Radiator"
        },
        {
            "trv_entity": "climate.trv_2",
            "valve_entity": "number.valve_2",
            "p_gain": 12.0,
            "i_gain": 0.7,
            "name": "Small Radiator"
        }
    ]
}
```

**Current Approach:**
```python
# Instance 1
{
    "name": "Living Room - Big Radiator",
    "trv_entity": "climate.trv_1",
    "reference_temp_entity": "sensor.living_room_temp",
    "target_temp_entity": "input_number.living_room_target",
    "valve_entity": "number.valve_1",
    "p_gain": 8.0,
    "i_gain": 0.3
}

# Instance 2  
{
    "name": "Living Room - Small Radiator",
    "trv_entity": "climate.trv_2",
    "reference_temp_entity": "sensor.living_room_temp",  # Duplicate
    "target_temp_entity": "input_number.living_room_target",  # Duplicate
    "valve_entity": "number.valve_2",
    "p_gain": 12.0,
    "i_gain": 0.7
}
```

### Coordinator Architecture

**Multi-TRV Approach:**
```python
class MultiTRVCoordinator:
    """One coordinator, multiple TRV controllers."""
    
    def __init__(self, ...):
        # Shared config
        self.reference_temp_entity = ...
        self.target_temp_entity = ...
        
        # Individual controllers
        self.trv_controllers = [
            TRVController(trv_1_config),  # Own PI state
            TRVController(trv_2_config),  # Own PI state
            TRVController(trv_3_config),  # Own PI state
        ]
    
    async def async_update_all(self):
        # Get shared values once
        ref_temp = get_state(self.reference_temp_entity)
        target_temp = get_state(self.target_temp_entity)
        
        # Update each TRV with its own PI controller
        for controller in self.trv_controllers:
            await controller.update(ref_temp, target_temp)
```

**Current Approach:**
```python
class TRVCoordinator:
    """One coordinator per TRV."""
    
    def __init__(self, trv_entity, reference, target, valve, p, i):
        self.trv_entity = trv_entity
        self.reference_temp_entity = reference
        self.target_temp_entity = target
        self.valve_entity = valve
        self._p_gain = p
        self._i_gain = i
        self._integrator = 0.0  # Own PI state
    
    async def async_update_data(self):
        # Get values (even if duplicate across instances)
        ref_temp = get_state(self.reference_temp_entity)
        target_temp = get_state(self.target_temp_entity)
        
        # Update this TRV only
        await self._update_trv(ref_temp, target_temp)
```

## Recommendation

### For v0.1.0 (Current Release): Keep Current Approach ✅

**Why:**
1. ✅ **Already implemented and working**
2. ✅ **Simpler code, easier to maintain**
3. ✅ **Standard HA patterns**
4. ✅ **Users can start using it now**
5. ✅ **Can always add multi-TRV later**

The "duplicate configuration" is not a real problem - it's just a few extra clicks during setup.

### For v0.2.0 (Future): Add Multi-TRV Option

**Implement both patterns:**
1. Keep current single-TRV config flow
2. Add new "Area" config flow with multi-TRV support
3. Let users choose their preference

**Migration path:**
- Users with single TRVs: Keep using simple flow
- Users with multiple TRVs per area: Use area flow
- Both supported simultaneously

## Implementation Effort

### Current Approach (Done ✅)
- Config flow: ✅ Implemented
- Coordinator: ✅ Implemented
- Entities: ✅ Implemented
- Options flow: ✅ Implemented
- Documentation: ✅ Complete

**Effort: 0 hours** (already done)

### Multi-TRV Approach
- Config flow: ~4-6 hours (multi-step with add/remove)
- Coordinator refactor: ~3-4 hours (list of controllers)
- Entities: ~2-3 hours (iterate over TRVs)
- Options flow: ~4-6 hours (edit list UI - most complex part)
- Testing: ~3-4 hours
- Documentation: ~2 hours

**Effort: ~20-25 hours**

## Decision Matrix

| Factor | Current | Multi-TRV | Winner |
|--------|---------|-----------|--------|
| Implementation time | 0 hours ✅ | 20-25 hours | Current |
| UX simplicity | Good | Better | Multi-TRV |
| Code complexity | Simple | Complex | Current |
| Maintenance | Easy | Moderate | Current |
| User setup time | +30s per TRV | Faster | Multi-TRV |
| Flexibility | High | Moderate | Current |
| Organization | Manual naming | Built-in | Multi-TRV |
| Already working | Yes ✅ | No | Current |

## Recommendation: Phased Approach

### Phase 1 (Now): Release v0.1.0 with Current Design ✅
- Get users using it
- Gather feedback
- See if multi-TRV is actually needed
- Establish user base

### Phase 2 (Later): Evaluate Multi-TRV
- If users ask for it → implement
- If current design works fine → keep it simple
- **Don't optimize prematurely!**

### Quote:
> "Make it work, make it right, make it fast - in that order."
> 
> You have "make it work" ✅
> 
> Wait for user feedback before "make it right"

## Conclusion

**For now: Ship what you have!** ✅🚀

The current design is:
- ✅ Functionally correct
- ✅ Well implemented
- ✅ Fully documented
- ✅ Ready to use

The multi-TRV approach is:
- ✨ Nice to have
- 🚧 Not yet implemented  
- ⏰ Significant work
- ❓ Might not be needed

**You can always add it later if users want it!**

