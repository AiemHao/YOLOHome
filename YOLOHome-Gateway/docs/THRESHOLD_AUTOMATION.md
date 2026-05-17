# Threshold Automation - Complete Guide

## Overview

The Threshold Automation feature allows you to automatically control devices based on sensor values. Each sensor can trigger multiple device actions simultaneously based on different conditions.

**Key Features:**
- Multiple rules per sensor (one sensor → many devices)
- Flexible threshold conditions (above, below, or both)
- Hysteresis support (prevent oscillation with above+below)
- Duplicate command prevention (no spam)
- Integer, float, and string number values supported

---

## Configuration Format

In `config.yml`, add the automation section:

```yaml
automation:
  threshold:
    enabled: true           # Enable threshold-based automation
  thresholds:
    <sensor_name>:          # Sensor to monitor
      - device: <device>    # Target device to control
        above: <value>      # (Optional) Trigger when > value
        below: <value>      # (Optional) Trigger when < value
        on_value: <value>   # Value to send when condition is TRUE
        off_value: <value>  # Value to send when condition is FALSE
```

---

## Examples

### 1. Simple Condition (Single Threshold)

```yaml
automation:
  threshold:
    enabled: true
  thresholds:
    temp:
      - device: fan
        above: 30           # Trigger when temperature > 30°C
        on_value: 1         # Turn fan ON (send 1)
        off_value: 0        # Turn fan OFF (send 0)
```

**Logic:**
- When temp > 30: `fan = 1` (ON)
- When temp ≤ 30: `fan = 0` (OFF)

---

### 2. Multiple Devices per Sensor

```yaml
automation:
  threshold:
    enabled: true
  thresholds:
    humi:
      - device: led
        above: 70
        below: 65
        on_value: 0
        off_value: 1
      
      - device: servo          # Second device for same sensor
        above: 70
        below: 65
        on_value: 1
        off_value: 0
```

**Logic for each device:**
- When 65 < humi < 70: `led = 1`, `servo = 0`
- When humi > 70: `led = 0`, `servo = 1`
- When humi < 65: `led = 0`, `servo = 1`

---

### 3. Hysteresis (Both above+below)

When you specify **both `above` and `below`**:
- Condition = `(value > above) OR (value < below)`
- This prevents oscillation around a single threshold

**Example: Temperature control with hysteresis**

```yaml
automation:
  threshold:
    enabled: true
  thresholds:
    temp:
      - device: ac
        above: 32          # Turn ON when > 32°C
        below: 28          # Turn ON when < 28°C  
        on_value: 1        # AC is running
        off_value: 0       # AC is OFF
```

**Behavior:**
| Temperature | Condition | AC State |
|---|---|---|
| 25°C | < 28 | ON (1) |
| 30°C | between 28-32 | OFF (0) |
| 35°C | > 32 | ON (1) |

This prevents the AC from constantly toggling at 30°C.

---

### 4. Light Sensor (0-100 range)

```yaml
automation:
  threshold:
    enabled: true
  thresholds:
    light:
      - device: led
        below: 30          # Dark: light level < 30
        on_value: 1        # Turn on LED (provide light)
        off_value: 0       # Turn off LED
```

**Logic:**
- When light < 30: `led = 1` (dark, LED ON)
- When light ≥ 30: `led = 0` (bright, LED OFF)

---

## Real-World Example: Complete Setup

```yaml
automation:
  threshold:
    enabled: true
  thresholds:
    # Temperature control - auto-fan
    temp:
      - device: fan
        above: 30
        on_value: 1
        off_value: 0

    # Humidity control - LED feedback + Servo position
    humi:
      - device: led
        above: 70          # High humidity
        below: 65          # Low humidity
        on_value: 0        # Red light when too dry or too wet
        off_value: 1       # Green light when OK
      
      - device: servo
        above: 70
        below: 65
        on_value: 1        # Activate dehumidifier
        off_value: 0       # Deactivate dehumidifier

    # Light control - auto LED
    light:
      - device: led
        below: 30          # Dark environment
        on_value: 1        # Provide light
        off_value: 0       # Natural light sufficient
```

---

## How It Works

### Processing Flow

1. **Serial receives sensor data:** `!T:28.5#` (temperature = 28.5°C)
2. **Parse sensor value:** Extract "28.5" from serial frame
3. **Check all rules for this sensor:**
   - Find all rules where `sensor == "temp"`
   - For each rule, evaluate the condition
4. **Execute actions:**
   - If condition is TRUE → send `on_value`
   - If condition is FALSE → send `off_value`
5. **Prevent duplicates:** Don't resend if same device got same value recently

### Condition Evaluation

```python
# For rule with above=30, below=28:
if temp > 30:
    # Condition TRUE → send on_value
elif temp < 28:
    # Condition TRUE → send on_value  
else:  # 28 ≤ temp ≤ 30
    # Condition FALSE → send off_value
```

**Truth table:**
| Condition | above | below | Result |
|---|---|---|---|
| value > above | ✓ | - | TRUE |
| value < below | - | ✓ | TRUE |
| above + below | ✓ | ✓ | (value > above) OR (value < below) |
| No condition | - | - | FALSE (log warning) |

---

## API & Integration

### ThresholdService Class

```python
from Controller.services import ThresholdService

# Initialize with config
config = {
    'temp': [
        {'device': 'fan', 'above': 30, 'on_value': 1, 'off_value': 0}
    ]
}
service = ThresholdService(config, enabled=True)

# Check threshold and execute callback
def send_command(device, value):
    print(f"Send {device}={value}")

service.check_threshold('temp', 35, send_command)  # Output: Send fan=1
```

### Key Methods

```python
# Check sensor value and trigger actions
service.check_threshold(sensor_name: str, value: Any, callback)

# Enable/disable automation globally
service.set_enabled(enabled: bool)
service.is_enabled() -> bool

# Manage rules
service.get_rules() -> List[Dict]
service.get_rules_for_sensor(sensor_name: str) -> List[Dict]
service.add_rule(rule: Dict)
service.remove_rule(device_name: str) -> bool
service.update_rule(device_name: str, rule: Dict) -> bool

# Get status
service.get_status() -> {'enabled': bool, 'rules_count': int, 'active_actions': dict}
```

---

## Troubleshooting

### 1. Rule Not Triggering

**Check:**
- Is automation `enabled: true` in config?
- Is the sensor name exactly matching the rule?
- Sensor names are **case-insensitive** (temp, TEMP, Temp all work)

**Debug:**
```python
status = service.get_status()
print(f"Service enabled: {status['enabled']}")
print(f"Rules count: {status['rules_count']}")
print(f"Active actions: {status['active_actions']}")
```

### 2. Command Sent Twice

**Expected behavior:** Duplicate commands are prevented automatically.
- Same device gets same value → command NOT sent
- Different value → command IS sent

**Reset if needed:**
```python
service.action_state.clear()  # Clear duplicate prevention cache
```

### 3. Unexpected Value Types

**Supported types:**
- Integer: `25`
- Float: `25.5`
- String number: `"25.5"`
- Invalid: `"abc"` → logs warning, ignored

---

## Testing

Run the comprehensive test suite:

```bash
cd YOLOHome-Gateway/GateWay
python -m pytest tests/test_threshold_rules.py -v
```

**Tests cover:**
- Config parsing (multiple sensors/devices)
- Single & multiple conditions (above, below, both)
- Hysteresis behavior
- Duplicate prevention
- Data type handling
- Case insensitivity
- Disable/enable toggling

---

## Performance Notes

- **Rate limited:** Prevents spam with configurable `rate_limit` settings
- **Stateful:** Tracks last sent value per device (no storage overhead)
- **Async:** Runs in serial→MQTT processing pipeline
- **Low overhead:** Simple threshold comparisons, no heavy computation

---

## Migration from Old Format

**Old format (still works):**
```yaml
thresholds:
  temp: {'above': 30, 'action_device': 'fan', 'action_value': '1'}
```

**New format (recommended):**
```yaml
thresholds:
  temp:
    - device: fan
      above: 30
      on_value: 1
      off_value: 0
```

The new format is more flexible and supports multiple devices per sensor.
