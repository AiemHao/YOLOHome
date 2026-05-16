"""
Test the new threshold service with the YAML config format.

Config format:
```yaml
automation:
  enabled: true
  thresholds:
    temp:
      - device: fan
        above: 30
        on_value: 1
        off_value: 0
    humi:
      - device: led
        above: 70
        below: 65
        on_value: 0
        off_value: 1
      - device: servo
        above: 70
        below: 65
        on_value: 1
        off_value: 0
    light:
      - device: led
        below: 30
        on_value: 1
        off_value: 0
```
"""

import pytest
from Controller.services import ThresholdService


class TestThresholdService:
    """Test threshold service with new config format."""

    def setup_method(self):
        """Set up test fixtures."""
        # Simulated config from config.yml
        self.config = {
            'temp': [
                {
                    'device': 'fan',
                    'above': 30,
                    'on_value': 1,
                    'off_value': 0
                }
            ],
            'humi': [
                {
                    'device': 'led',
                    'above': 70,
                    'below': 65,
                    'on_value': 0,
                    'off_value': 1
                },
                {
                    'device': 'servo',
                    'above': 70,
                    'below': 65,
                    'on_value': 1,
                    'off_value': 0
                }
            ],
            'light': [
                {
                    'device': 'led',
                    'below': 30,
                    'on_value': 1,
                    'off_value': 0
                }
            ]
        }
        
        self.service = ThresholdService(self.config, enabled=True)
        self.commands_sent = []

    def send_command(self, device, value):
        """Mock command callback."""
        self.commands_sent.append({'device': device, 'value': value})

    def test_parse_config(self):
        """Test that config is parsed correctly."""
        assert len(self.service.rules) == 4  # 1 temp + 2 humi + 1 light
        
        # Check parsed rules
        rules_by_sensor = {}
        for rule in self.service.rules:
            sensor = rule['sensor']
            if sensor not in rules_by_sensor:
                rules_by_sensor[sensor] = []
            rules_by_sensor[sensor].append(rule)
        
        assert len(rules_by_sensor['temp']) == 1
        assert len(rules_by_sensor['humi']) == 2
        assert len(rules_by_sensor['light']) == 1

    def test_temp_above_30(self):
        """Test temperature sensor with 'above' condition."""
        # Temp = 35 (> 30) → fan = 1
        self.service.check_threshold('temp', 35, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0] == {'device': 'fan', 'value': 1}
        
        # Reset
        self.commands_sent.clear()
        
        # Temp = 25 (< 30) → fan = 0
        self.service.check_threshold('temp', 25, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0] == {'device': 'fan', 'value': 0}

    def test_humi_both_conditions(self):
        """Test humidity sensor with both above and below conditions (hysteresis).
        
        When both above and below are specified:
        - Condition = value > above OR value < below
        - If above=70 and below=65:
          - value=75: 75 > 70 → True → on_value
          - value=67: not (67 > 70 or 67 < 65) → False → off_value
          - value=60: 60 < 65 → True → on_value
        """
        # Humidity = 75 (> 70) → led = 0, servo = 1
        self.service.check_threshold('humi', 75, self.send_command)
        assert len(self.commands_sent) == 2
        assert {'device': 'led', 'value': 0} in self.commands_sent
        assert {'device': 'servo', 'value': 1} in self.commands_sent
        
        self.commands_sent.clear()
        
        # Humidity = 67 (between 65 and 70) → led = 1, servo = 0
        self.service.check_threshold('humi', 67, self.send_command)
        assert len(self.commands_sent) == 2
        assert {'device': 'led', 'value': 1} in self.commands_sent
        assert {'device': 'servo', 'value': 0} in self.commands_sent
        
        self.commands_sent.clear()
        
        # Humidity = 60 (< 65) → led = 0, servo = 1
        self.service.check_threshold('humi', 60, self.send_command)
        assert len(self.commands_sent) == 2
        assert {'device': 'led', 'value': 0} in self.commands_sent
        assert {'device': 'servo', 'value': 1} in self.commands_sent

    def test_light_below_30(self):
        """Test light sensor with 'below' condition."""
        # Light = 25 (< 30) → led = 1
        self.service.check_threshold('light', 25, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0] == {'device': 'led', 'value': 1}
        
        self.commands_sent.clear()
        
        # Light = 50 (> 30) → led = 0
        self.service.check_threshold('light', 50, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0] == {'device': 'led', 'value': 0}

    def test_no_duplicate_commands(self):
        """Test that same command is not sent twice."""
        # First: temp = 35 → fan = 1
        self.service.check_threshold('temp', 35, self.send_command)
        assert len(self.commands_sent) == 1
        
        # Second: temp = 40 → fan should stay 1 (same value, no send)
        self.service.check_threshold('temp', 40, self.send_command)
        assert len(self.commands_sent) == 1  # No new command sent
        
        # Third: temp = 20 → fan = 0 (different value, send)
        self.service.check_threshold('temp', 20, self.send_command)
        assert len(self.commands_sent) == 2

    def test_disabled_service(self):
        """Test that disabled service doesn't send commands."""
        self.service.set_enabled(False)
        self.service.check_threshold('temp', 35, self.send_command)
        assert len(self.commands_sent) == 0
        
        # Enable and test again
        self.service.set_enabled(True)
        self.service.check_threshold('temp', 35, self.send_command)
        assert len(self.commands_sent) == 1

    def test_case_insensitive_sensor_names(self):
        """Test that sensor names are case-insensitive."""
        # Should work with different cases
        self.service.check_threshold('TEMP', 35, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0]['device'] == 'fan'

    def test_get_rules_for_sensor(self):
        """Test retrieving rules for a specific sensor."""
        temp_rules = self.service.get_rules_for_sensor('temp')
        assert len(temp_rules) == 1
        assert temp_rules[0]['device'] == 'fan'
        
        humi_rules = self.service.get_rules_for_sensor('humi')
        assert len(humi_rules) == 2
        devices = [r['device'] for r in humi_rules]
        assert 'led' in devices
        assert 'servo' in devices

    def test_get_status(self):
        """Test getting service status."""
        status = self.service.get_status()
        assert status['enabled'] is True
        assert status['rules_count'] == 4  # 1 temp + 2 humi + 1 light
        assert isinstance(status['active_actions'], dict)

    def test_numeric_data_types(self):
        """Test that numeric types (int, float, string numbers) work."""
        # Integer
        self.service.check_threshold('temp', 35, self.send_command)
        assert len(self.commands_sent) == 1
        
        # Reset state for next test
        self.service.action_state.clear()
        self.commands_sent.clear()
        
        # Float - use a different value to trigger a state change
        self.service.check_threshold('temp', 20, self.send_command)
        assert len(self.commands_sent) == 1
        
        # Reset state for next test
        self.service.action_state.clear()
        self.commands_sent.clear()
        
        # String number
        self.service.check_threshold('temp', '35.5', self.send_command)
        assert len(self.commands_sent) == 1

    def test_non_numeric_sensor_value(self):
        """Test that non-numeric sensor values are skipped."""
        self.service.check_threshold('temp', 'invalid', self.send_command)
        assert len(self.commands_sent) == 0

    def test_light_range_0_100(self):
        """Test light sensor with range 0-100."""
        # Light is integer 0-100
        # Light = 20 (< 30) → led = 1
        self.service.check_threshold('light', 20, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0]['value'] == 1
        
        self.commands_sent.clear()
        
        # Light = 100 (> 30) → led = 0
        self.service.check_threshold('light', 100, self.send_command)
        assert len(self.commands_sent) == 1
        assert self.commands_sent[0]['value'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
