# Threshold Automation Rules Guide

## Overview

The Threshold Service supports **multiple rules for multiple devices**. Each rule can:
- Watch **one or more sensors**
- Have **complex conditions** (above, below, range, equals)
- Trigger **multiple actions on different devices**

## Rule Structure

```python
{
    "id": "rule_1",                          # Unique rule identifier (required)
    "enabled": True,                         # Enable/disable this specific rule
    "sensors": ["temperature"],              # One or more sensors to watch
    "conditions": {
        "type": "above",                     # Condition type: "above", "below", "range", "equals"
        "value": 30,                         # Threshold value
        "value_high": 35                     # For "range" type only
    },
    "actions": [                             # Multiple actions for multiple devices
        {
            "device": "fan",                 # Target device to control
            "command": "on"                  # Command to send
        },
        {
            "device": "ac",                  # Another device
            "command": "cool"
        }
    ]
}
```

## Examples

### Example 1: Temperature Control (One Sensor, Multiple Devices)

When temperature exceeds 30°C, turn on both fan and AC:

```python
rules = [
    {
        "id": "high_temp_cooling",
        "enabled": True,
        "sensors": ["temperature"],
        "conditions": {
            "type": "above",
            "value": 30
        },
        "actions": [
            {"device": "fan", "command": "on"},
            {"device": "ac", "command": "cool"}
        ]
    },
    {
        "id": "low_temp_heating",
        "enabled": True,
        "sensors": ["temperature"],
        "conditions": {
            "type": "below",
            "value": 15
        },
        "actions": [
            {"device": "heater", "command": "on"}
        ]
    }
]
```

### Example 2: Humidity Control with Range

Maintain humidity between 40-60%, activate dehumidifier above 70%:

```python
rules = [
    {
        "id": "humidity_control",
        "enabled": True,
        "sensors": ["humidity"],
        "conditions": {
            "type": "above",
            "value": 70
        },
        "actions": [
            {"device": "dehumidifier", "command": "on"}
        ]
    }
]
```

### Example 3: Multiple Sensors, Same Device

Different sensors can control the same device with different rules:

```python
rules = [
    {
        "id": "temp_fan_control",
        "enabled": True,
        "sensors": ["temperature"],
        "conditions": {
            "type": "above",
            "value": 30
        },
        "actions": [
            {"device": "fan", "command": "on"}
        ]
    },
    {
        "id": "humidity_fan_control",
        "enabled": True,
        "sensors": ["humidity"],
        "conditions": {
            "type": "above",
            "value": 70
        },
        "actions": [
            {"device": "fan", "command": "high"}  # Different command
        ]
    }
]
```

### Example 4: Light Control with Range

Turn on lights when ambient light level is in the twilight range (100-500 lux):

```python
rules = [
    {
        "id": "twilight_light_control",
        "enabled": True,
        "sensors": ["light_level"],
        "conditions": {
            "type": "range",
            "value": 100,           # Minimum
            "value_high": 500       # Maximum
        },
        "actions": [
            {"device": "lights", "command": "dim"}
        ]
    }
]
```

## Condition Types

### "above"
Trigger when sensor value > threshold value

```python
"conditions": {
    "type": "above",
    "value": 30
}
```

### "below"
Trigger when sensor value < threshold value

```python
"conditions": {
    "type": "below",
    "value": 20
}
```

### "range"
Trigger when threshold value ≤ sensor value ≤ value_high

```python
"conditions": {
    "type": "range",
    "value": 100,
    "value_high": 500
}
```

### "equals"
Trigger when sensor value ≈ threshold value (within 0.01)

```python
"conditions": {
    "type": "equals",
    "value": 1
}
```

## API Usage

### Initialize with Rules

```python
from Controller.services import ThresholdService

rules = [
    {
        "id": "rule_1",
        "sensors": ["temperature"],
        "conditions": {"type": "above", "value": 30},
        "actions": [{"device": "fan", "command": "on"}]
    }
]

service = ThresholdService(threshold_rules=rules, enabled=True)
```

### Check Thresholds

```python
def send_command(device, command):
    # Send command to device
    mqtt_client.publish(f"home/device/{device}", command)

# When sensor value updates
service.check_threshold("temperature", 32.5, send_command)
```

### Manage Rules at Runtime

```python
# Get all rules
all_rules = service.get_rules()

# Get rules for specific sensor
temp_rules = service.get_rules_for_sensor("temperature")

# Add a new rule
new_rule = {
    "id": "pressure_control",
    "sensors": ["pressure"],
    "conditions": {"type": "above", "value": 1000},
    "actions": [{"device": "valve", "command": "open"}]
}
service.add_rule(new_rule)

# Get rule by ID
rule = service.get_rule_by_id("rule_1")

# Update existing rule
updated_rule = {...}
service.update_rule("rule_1", updated_rule)

# Remove rule
service.remove_rule("rule_1")
```

### Enable/Disable

```python
# Disable all threshold automation
service.set_enabled(False)

# Enable specific rule by modifying and updating
rule = service.get_rule_by_id("rule_1")
rule["enabled"] = False
service.update_rule("rule_1", rule)
```

### Get Status

```python
status = service.get_status()
# Returns:
# {
#     'enabled': True,
#     'rules_count': 3,
#     'active_actions': {'fan': 'on', 'ac': 'cool'}
# }
```

## Best Practices

1. **Unique IDs**: Always assign unique rule IDs for management
2. **Descriptive Names**: Use clear ID names that describe the rule's purpose
3. **Enable/Disable Flag**: Use the `enabled` flag to toggle rules without removing them
4. **Single Responsibility**: Keep rules focused on specific automations
5. **Test Thresholds**: Test edge cases around threshold values
6. **Duplicate Prevention**: The service automatically prevents duplicate commands to the same device
7. **Sensor Name Consistency**: Use consistent sensor naming across your system

## Configuration File Example (config.yml)

```yaml
threshold_rules:
  - id: "temperature_cooling"
    enabled: true
    sensors:
      - "temperature"
    conditions:
      type: "above"
      value: 30
    actions:
      - device: "fan"
        command: "on"
      - device: "ac"
        command: "cool"
  
  - id: "humidity_dehumidify"
    enabled: true
    sensors:
      - "humidity"
    conditions:
      type: "above"
      value: 70
    actions:
      - device: "dehumidifier"
        command: "on"
  
  - id: "light_dimming"
    enabled: true
    sensors:
      - "light_level"
    conditions:
      type: "range"
      value: 100
      value_high: 500
    actions:
      - device: "lights"
        command: "dim"
```

## Troubleshooting

### Rule Not Triggering
1. Check if service is enabled: `service.is_enabled()`
2. Check if rule is enabled: `service.get_rule_by_id("rule_id")['enabled']`
3. Verify sensor name matches exactly (case-insensitive check still applied)
4. Check condition type and value are correct
5. Monitor logs for warnings about non-numeric values

### Commands Not Sending
1. Check rate limiting (may buffer frequent changes)
2. Verify device names are correct
3. Check MQTT connectivity
4. Verify device exists in managed devices list

### Multiple Rules Conflicting
- Use `enabled` flag to disable conflicting rules
- Ensure different rules have non-conflicting conditions
- Monitor `active_actions` to see current device states
