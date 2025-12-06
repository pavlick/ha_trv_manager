# TRV Manager Dashboard Examples

## Simple Monitoring Card

Once you've enabled the diagnostic sensors, add this card to your dashboard:

### Option 1: Entities Card (Simple)

```yaml
type: entities
title: TRV Manager - Living Room
entities:
  # Replace with your actual entity IDs
  - entity: sensor.living_room_trv_manager_error
    name: Temperature Error
    icon: mdi:thermometer-alert
  - entity: sensor.living_room_trv_manager_temp_adjustment
    name: TRV Adjustment
    icon: mdi:thermometer-chevron-up
  - entity: sensor.living_room_trv_manager_valve_output
    name: Valve Position
    icon: mdi:valve
  - entity: sensor.living_room_trv_manager_integrator
    name: Integrator
    icon: mdi:counter
  - type: divider
  - entity: number.living_room_trv_manager_p_gain
    name: P Gain
  - entity: number.living_room_trv_manager_i_gain
    name: I Gain
```

### Option 2: Detailed Grid Card

```yaml
type: grid
columns: 2
square: false
cards:
  # Current Status
  - type: entity
    entity: sensor.living_room_trv_manager_error
    name: Temperature Error
    icon: mdi:thermometer-alert
    
  - type: entity
    entity: sensor.living_room_trv_manager_temp_adjustment
    name: TRV Compensation
    icon: mdi:thermometer-chevron-up
    
  - type: entity
    entity: sensor.living_room_trv_manager_valve_output
    name: Valve Position
    icon: mdi:valve
    
  - type: entity
    entity: sensor.living_room_trv_manager_integrator
    name: Integrator
    icon: mdi:counter
    
  # PI Controller Settings
  - type: entity
    entity: number.living_room_trv_manager_p_gain
    name: P Gain
    icon: mdi:tune
    
  - type: entity
    entity: number.living_room_trv_manager_i_gain
    name: I Gain
    icon: mdi:tune-vertical
```

### Option 3: Comprehensive Monitoring (With Context)

```yaml
type: vertical-stack
cards:
  # Title
  - type: markdown
    content: |
      ## TRV Manager - Living Room
      Real-time monitoring and control
      
  # Temperature Overview
  - type: entities
    title: Temperature Status
    entities:
      - entity: sensor.living_room_temperature
        name: Room Temperature (Reference)
        icon: mdi:thermometer
      - entity: input_number.living_room_target_temp
        name: Target Temperature
        icon: mdi:target
      - entity: climate.living_room_trv
        name: TRV Reading
        icon: mdi:radiator
      - entity: sensor.living_room_trv_manager_error
        name: Error (Target - Reference)
        icon: mdi:delta
        
  # Compensation & Control
  - type: entities
    title: TRV Manager Control
    entities:
      - entity: sensor.living_room_trv_manager_temp_adjustment
        name: Temperature Compensation
        icon: mdi:thermometer-plus
      - entity: sensor.living_room_trv_manager_valve_output
        name: Valve Position (PI Output)
        icon: mdi:valve
      - entity: sensor.living_room_trv_manager_integrator
        name: Integrator Value
        icon: mdi:counter
        
  # PI Tuning
  - type: entities
    title: PI Controller Tuning
    entities:
      - entity: number.living_room_trv_manager_p_gain
        name: Proportional Gain
        icon: mdi:tune
      - entity: number.living_room_trv_manager_i_gain
        name: Integral Gain
        icon: mdi:tune-vertical
```

### Option 4: History Graph (Best for Understanding Behavior)

```yaml
type: history-graph
title: TRV Manager Performance
hours_to_show: 6
entities:
  - entity: sensor.living_room_temperature
    name: Room Temp
  - entity: input_number.living_room_target_temp
    name: Target
  - entity: sensor.living_room_trv_manager_error
    name: Error
  - entity: sensor.living_room_trv_manager_valve_output
    name: Valve %
```

### Option 5: Gauge Cards for Quick Glance

```yaml
type: horizontal-stack
cards:
  - type: gauge
    entity: sensor.living_room_trv_manager_error
    name: Temperature Error
    min: -5
    max: 5
    needle: true
    segments:
      - from: -5
        color: '#0080ff'
      - from: -1
        color: '#00cc00'
      - from: 1
        color: '#ff8000'
      - from: 3
        color: '#ff0000'
        
  - type: gauge
    entity: sensor.living_room_trv_manager_valve_output
    name: Valve Position
    min: 0
    max: 100
    unit: '%'
    needle: true
    segments:
      - from: 0
        color: '#0080ff'
      - from: 25
        color: '#00cc00'
      - from: 75
        color: '#ff8000'
      - from: 90
        color: '#ff0000'
```

## Understanding the Sensors

### Temperature Error
- **What it is**: Target temperature minus reference temperature
- **Positive value**: Room is too cold (heating needed)
- **Negative value**: Room is too warm (reduce heating)
- **Zero**: Perfect! Room at target temperature

### Temperature Adjustment
- **What it is**: The compensation applied to TRV target
- **Shows**: How much the TRV reading differs from room reading
- **Example**: If +1.3°C, the TRV reads 1.3° higher than actual room temp

### Valve Position Output
- **What it is**: PI controller output (0-100%)
- **Only useful if**: You have valve position control configured
- **0%**: Valve fully closed
- **100%**: Valve fully open
- **Shows**: How hard the system is working to reach target

### Integrator Value
- **What it is**: Accumulated error over time (internal PI state)
- **Increasing**: System trying harder to eliminate error
- **Decreasing**: Error reducing or anti-windup active
- **Use case**: Advanced tuning and troubleshooting

## Quick Assessment Guide

### System Working Well:
- ✅ Error oscillates around 0 (±0.5°C)
- ✅ Temperature adjustment stays relatively stable
- ✅ Valve position adjusts smoothly (not jumping 0↔100)
- ✅ Room temperature tracks target temperature

### System Needs Tuning:
- ⚠️ Error oscillates wildly (±2°C or more) → Reduce P gain
- ⚠️ Error never reaches 0 → Increase I gain
- ⚠️ Valve constantly at 0% or 100% → Adjust both gains
- ⚠️ Temperature overshoots target → Reduce I gain

## Automation Example: Alert on Poor Performance

```yaml
automation:
  - alias: "Alert: TRV Error Too High"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_trv_manager_error
        above: 2
        for:
          minutes: 15
    action:
      - service: notify.notify
        data:
          title: "TRV Manager Alert"
          message: "Living room is {{ states('sensor.living_room_trv_manager_error') }}°C below target for 15 minutes. Check heating system."
```

## Tips for Monitoring

1. **Start Simple**: Use the Entities Card first to see all values
2. **Add History**: After a few hours, add history graphs to see trends
3. **Watch for Patterns**: Look at how the system responds to target changes
4. **Tune if Needed**: Use the diagnostic sensors to guide P/I gain adjustments
5. **Compare Multiple TRVs**: If you have multiple TRVs, compare their behavior

## Example Entity IDs Format

Your actual entity IDs will follow this pattern:
- `sensor.{name}_error`
- `sensor.{name}_integrator`
- `sensor.{name}_temp_adjustment`
- `sensor.{name}_valve_output`
- `number.{name}_p_gain`
- `number.{name}_i_gain`

Where `{name}` is the slugified version of the name you entered during setup (lowercase, spaces replaced with underscores).

