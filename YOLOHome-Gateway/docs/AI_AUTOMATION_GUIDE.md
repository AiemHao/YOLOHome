# AI Automation Integration Guide

## Overview

YOLOHome Gateway now supports **AI-based automation** using a trained Decision Tree model for smart curtain control. You can choose between two automation modes:

1. **Threshold Mode** (Default): Rule-based automation with sensor thresholds
2. **AI Mode**: Machine Learning-based automation using a Decision Tree model

## Quick Start

### Enable AI Mode

1. **Modify `config.yml`**:
   ```yaml
   automation:
     threshold:
       enabled: true
     ai:
       enabled: true  # Set to true to enable AI
       model_path: "GateWay/Decision_tree/models/curtain_model.pkl"
   ```

2. **Restart the Gateway**:
   ```bash
   python GateWay/run.py
   ```

### Disable AI Mode (Back to Threshold)

1. **Modify `config.yml`**:
   ```yaml
   automation:
     threshold:
       enabled: true
     ai:
       enabled: false  # Set to false to use threshold rules
   ```

2. **Restart the Gateway**

## How It Works

### Threshold Mode (Default)
- Uses **rule-based thresholds** for each sensor (temperature, humidity, light)
- Fixed rules defined in `config.yml`
- Example: "If light > 70%, close curtain"
- Predictable and easy to understand

### AI Mode
- Uses a **trained Decision Tree model** for intelligent decisions
- Takes 3 sensor inputs: light (%), temperature (°C), humidity (%)
- Outputs: 0 (close curtain) or 1 (open curtain)
- Learns optimal control patterns from synthetic data
- More adaptable to complex conditions

## Configuration

### Configuration File: `config.yml`

```yaml
automation:
  threshold:
    enabled: true                                         # Enable threshold-based automation
  ai:
    enabled: false                                        # Enable AI-based automation
    model_path: "GateWay/Decision_tree/models/curtain_model.pkl"  # Model location
  
  thresholds:                                            # Used when AI is disabled
    temp:
      - device: fan
        above: 30
        on_value: 1
        off_value: 0
    # ... other threshold rules
```

### Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `automation.threshold.enabled` | bool | Enable threshold-based automation |
| `automation.ai.enabled` | bool | Enable AI-based automation |
| `automation.ai.model_path` | string | Path to trained Decision Tree model pickle file |

## Model Training

### Training the Decision Tree Model

The training script generates synthetic data and trains a Decision Tree classifier:

```bash
cd YOLOHome-Gateway/GateWay/Decision_tree
python curtain_control_system.py
```

### What the Training Script Does

1. **Generates synthetic training data** (10,000 samples)
   - Based on 7 predefined control rules
   - Covers the full sensor range

2. **Trains Decision Tree model**
   - Algorithm: sklearn.tree.DecisionTreeClassifier
   - Hyperparameters: max_depth=10, min_samples_split=20, min_samples_leaf=10

3. **Evaluates accuracy**
   - Internal validation: ~99.95% accuracy
   - External test set: ~99.90% accuracy

4. **Saves model** to `models/curtain_model.pkl`

### Training Data

The model is trained on 7 control rules:

| Rule | Condition | Action | Reason |
|------|-----------|--------|--------|
| 1 | Light > 70% | Close | Avoid glare & UV damage |
| 2 | Light < 30% + Temp 20-30°C | Open | Maximize natural light |
| 3 | Temp > 35°C + Humi < 50% | Close | Cool the room |
| 4 | Temp < 5°C | Close | Reduce heat loss |
| 5 | Humi > 80% | Open | Improve air circulation |
| 6 | Temp 20-30°C + Humi 40-60% | Open | Optimal comfort zone |
| 7 | Temp 30-35°C + Humi 50-70% | Close | Maintain comfort |

## API Usage

### Enable/Disable AI at Runtime

#### Using MQTT

```bash
# Enable AI mode
mosquitto_pub -t home/system/ai/set -m "enable"

# Disable AI mode (back to threshold)
mosquitto_pub -t home/system/ai/set -m "disable"

# Get current automation status
mosquitto_pub -t home/system/status/request -m "automation"
```

#### Using Python API

```python
from GateWay.Controller.controller import MainController

# Enable AI
controller.set_ai_enabled(True)

# Disable AI
controller.set_ai_enabled(False)

# Check if AI is active
is_ai_active = controller.is_ai_enabled()

# Get full automation status
status = controller.get_automation_status()
print(status)
# Output:
# {
#   'threshold': {'enabled': True, ...},
#   'ai': {'enabled': True, 'model_loaded': True, ...},
#   'active_mode': 'AI'
# }
```

## Sensor Inputs

The AI model requires these sensor values (updated from serial device):

| Sensor | Map Key | Range | Unit | Frequency |
|--------|---------|-------|------|-----------|
| Light Sensor | `light` | 0-100 | % | Every sensor update |
| Temperature | `temp` | -10 to 50 | °C | Every sensor update |
| Humidity | `humi` | 0-100 | % | Every sensor update |

Example sensor data:
```json
{
  "light": 75.5,
  "temp": 28.2,
  "humi": 65.3
}
```

## Device Control

Both modes control the **servo (curtain)** device:

- **Action 0**: Close curtain
- **Action 1**: Open curtain

MQTT Topic: `home/livingroom/device/servo/set`

## Troubleshooting

### AI Mode Not Activating

1. **Check model file exists**:
   ```
   YOLOHome-Gateway/GateWay/Decision_tree/models/curtain_model.pkl
   ```

2. **Check configuration**:
   ```yaml
   automation:
     threshold:
       enabled: true
     ai:
       enabled: true
       model_path: "GateWay/Decision_tree/models/curtain_model.pkl"
   ```

3. **Verify startup logs**:
   ```
   AI config: enabled=True, model=GateWay/Decision_tree/models/curtain_model.pkl
   AI service: Model loaded ✓
   Automation: AI mode (Threshold: False, AI: True)
   ```

### Model Accuracy Issues

1. **Retrain the model**:
   ```bash
   python GateWay/Decision_tree/curtain_control_system.py
   ```

2. **Check training output** for accuracy metrics
   - Should be >99% on test set
   - If lower, check for data generation issues

### Sensor Data Missing

- AI mode requires all 3 sensors: light, temp, humidity
- If any sensor missing, falls back to threshold mode
- Check that sensors are properly mapped in `config.yml`

## Performance Comparison

### Threshold Mode
- ✓ Deterministic and predictable
- ✓ Easily configurable without ML knowledge
- ✗ Rigid rules that can't adapt
- ✗ May miss optimal combinations

### AI Mode
- ✓ Learns optimal patterns
- ✓ Handles complex interactions
- ✓ ~99.9% accuracy on trained patterns
- ✗ Requires trained model
- ✗ Black-box decisions

## File Structure

```
YOLOHome-Gateway/
├── config.yml                          # Main configuration
├── config.docker.yml                   # Docker configuration
├── GateWay/
│   ├── run.py                          # Gateway startup script
│   ├── Controller/
│   │   ├── controller.py               # Main message router (with AI support)
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ai_service.py           # AI automation service (NEW)
│   │       ├── threshold_service.py    # Threshold automation
│   │       └── ...
│   └── Decision_tree/
│       ├── curtain_control_system.py   # Training script
│       ├── data/
│       │   ├── curtain_train.csv      # Training data
│       │   └── curtain_test.csv       # Test data
│       └── models/
│           └── curtain_model.pkl      # Trained model (NEW)
└── docs/
    └── AI_AUTOMATION_GUIDE.md         # This file
```

## Examples

### Example 1: Daytime (Bright, Hot, Dry)

Input:
```
Light: 85%
Temp: 33°C
Humidity: 45%
```

**Threshold Mode**: Checks light > 70% → Close curtain

**AI Mode**: Recognizes "bright & hot" → Close curtain

**Result**: Same action, but AI considers all factors

### Example 2: Overcast Morning (Dim, Mild, Humid)

Input:
```
Light: 35%
Temp: 22°C
Humidity: 72%
```

**Threshold Mode**: No threshold triggered → No action

**AI Mode**: Recognizes "dim, mild, slightly humid" → Open curtain

**Result**: AI provides better comfort by opening for natural light

## References

- Decision Tree Model: `GateWay/Decision_tree/curtain_control_system.py`
- AI Service: `GateWay/Controller/services/ai_service.py`
- Main Controller: `GateWay/Controller/controller.py`
- Configuration: `config.yml` and `config.docker.yml`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review gateway logs (log level: INFO or DEBUG)
3. Test sensor data with sample values
4. Retrain model if needed
