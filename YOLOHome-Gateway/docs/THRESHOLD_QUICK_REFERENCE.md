# Threshold Automation - Quick Reference

## Basic Config

```yaml
automation:
  threshold:
    enabled: true
  thresholds:
    sensor_name:
      - device: device_name
        above: 30              # Condition: value > 30
        on_value: 1            # Send this when true
        off_value: 0           # Send this when false
```

## Condition Types

| Condition | Config | Trigger |
|---|---|---|
| Simple high | `above: 30` | value > 30 |
| Simple low | `below: 30` | value < 30 |
| Hysteresis | `above: 32, below: 28` | value > 32 OR value < 28 |

## Common Patterns

### Temperature Control
```yaml
temp:
  - device: fan
    above: 30      # Cool when hot
    on_value: 1
    off_value: 0
```

### Light Control  
```yaml
light:
  - device: led
    below: 30      # LED on when dark
    on_value: 1
    off_value: 0
```

### Humidity with Hysteresis
```yaml
humi:
  - device: dehumidifier
    above: 70      # Too wet
    below: 40      # Too dry
    on_value: 1    # Run dehumidifier if too wet or too dry
    off_value: 0   # Off if in range 40-70
```

### Multiple Devices per Sensor
```yaml
humi:
  - device: led       # Device 1: indicator light
    above: 70
    below: 65
    on_value: 0       # Red = bad
    off_value: 1      # Green = good
  
  - device: fan       # Device 2: dehumidifier
    above: 70
    below: 65
    on_value: 1       # Run if out of range
    off_value: 0
```

## Python Usage

```python
from Controller.services import ThresholdService

# Initialize
service = ThresholdService(config_dict, enabled=True)

# Process sensor reading
def on_command(device, value):
    print(f"Control {device}={value}")

service.check_threshold('temp', 35, on_command)

# Manage
service.set_enabled(False)                    # Disable all
service.get_rules_for_sensor('temp')          # Get sensor rules
service.get_status()                          # Status check
```

## Value Types

| Type | Example | Valid |
|---|---|---|
| Integer | `1`, `0`, `100` | ✓ |
| Float | `25.5`, `72.3` | ✓ |
| String number | `"30"`, `"72.5"` | ✓ |
| Boolean | `true`, `false` | ✓ |
| Invalid | `"abc"` | ✗ Ignored |

## Common Issues

| Issue | Solution |
|---|---|
| Rule not working | Check `enabled: true`, verify sensor name |
| Command sent too much | Normal - duplicate prevention active |
| Wrong device triggered | Check device name in rule (case-insensitive) |
| Value parsing error | Use numeric values or string numbers |

## Full Example

```yaml
# config.yml
automation:
  threshold:
    enabled: true
  thresholds:
    temp:
      - device: fan
        above: 30
        on_value: 1
        off_value: 0
    
    light:
      - device: led
        below: 30
        on_value: 1
        off_value: 0
    
    humi:
      - device: servo
        above: 70
        below: 65
        on_value: 1
        off_value: 0
```

**Behavior:**
- temp > 30°C → fan ON
- light < 30 lux → led ON  
- humi > 70% or < 65% → servo ON
