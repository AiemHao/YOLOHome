"""Test cases for MainController threshold integration."""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Controller.controller import MainController
from Adapter.default_adapter import DefaultDataAdapter


class TestMainControllerThreshold(unittest.TestCase):
    """Test cases for MainController threshold functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = DefaultDataAdapter()
        self.mqtt_client = MagicMock()
        self.serial_module = MagicMock()

        self.threshold_rules = {
            'temp': {
                'device': 'fan',
                'above': 30,
                'below': 25,
                'on_value': '1',
                'off_value': '0'
            }
        }

        self.managed_devices = {
            'temp': {'type': 'sensor', 'serial_abbr': 'T', 'is_switch': False},
            'fan': {'type': 'device', 'serial_abbr': 'F', 'is_switch': True},
        }

        self.controller = MainController(
            mqtt_client=self.mqtt_client,
            serial_module=self.serial_module,
            data_adapter=self.adapter,
            managed_devices=self.managed_devices,
            threshold_rules=self.threshold_rules
        )

    def test_threshold_initialization(self):
        """Test threshold service is properly initialized."""
        self.assertTrue(self.controller.is_threshold_enabled())
        self.assertEqual(self.controller.get_threshold_rules(), self.threshold_rules)

    def test_threshold_enabled_disabled(self):
        """Test enabling/disabling threshold automation."""
        self.controller.set_threshold_enabled(False)
        self.assertFalse(self.controller.is_threshold_enabled())

        self.controller.set_threshold_enabled(True)
        self.assertTrue(self.controller.is_threshold_enabled())

    def test_threshold_status(self):
        """Test getting threshold status."""
        status = self.controller.get_threshold_status()
        self.assertEqual(status['enabled'], True)
        self.assertEqual(status['rules_count'], 1)
        self.assertEqual(status['active_actions'], {})

    def test_threshold_integration_serial_callback(self):
        """Test threshold triggers during serial data processing."""
        # Mock the _to_serial method to track calls
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Simulate receiving temp=35 from serial
            self.controller._on_serial("!T:35#")

            # Should trigger fan on
            mock_to_serial.assert_called_once_with('fan', '1')

    def test_threshold_no_trigger_when_disabled(self):
        """Test threshold does not trigger when disabled."""
        self.controller.set_threshold_enabled(False)

        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Simulate receiving temp=35 from serial
            self.controller._on_serial("!T:35#")

            # Should not trigger
            mock_to_serial.assert_not_called()

    def test_threshold_no_trigger_within_range(self):
        """Test threshold does not trigger when value is within range."""
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Simulate receiving temp=27 (within 25-30 range)
            self.controller._on_serial("!T:27#")

            # Should not trigger
            mock_to_serial.assert_not_called()

    def test_threshold_below_trigger(self):
        """Test threshold triggers when value goes below threshold."""
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Simulate receiving temp=20 (below 25)
            self.controller._on_serial("!T:20#")

            # Should trigger fan off
            mock_to_serial.assert_called_once_with('fan', '0')

    def test_threshold_rate_limiting(self):
        """Test threshold respects rate limiting."""
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=False):

            # Simulate receiving temp=35 from serial
            self.controller._on_serial("!T:35#")

            # Should not trigger due to rate limiting
            mock_to_serial.assert_not_called()

    def test_threshold_non_sensor_device(self):
        """Test threshold does not trigger for non-sensor devices."""
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Simulate receiving fan=1 from serial (fan is device, not sensor)
            self.controller._on_serial("!F:1#")

            # Should not trigger threshold check
            mock_to_serial.assert_not_called()

    def test_threshold_invalid_value(self):
        """Test threshold handles invalid sensor values."""
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Simulate receiving invalid temp value
            self.controller._on_serial("!T:invalid#")

            # Should not trigger
            mock_to_serial.assert_not_called()

    def test_threshold_unknown_device(self):
        """Test threshold does not trigger for unknown target device."""
        # Create controller with rule pointing to unknown device
        bad_rules = {
            'temp': {
                'device': 'unknown_device',
                'above': 30,
                'below': 25,
                'on_value': '1',
                'off_value': '0'
            }
        }

        controller = MainController(
            mqtt_client=self.mqtt_client,
            serial_module=self.serial_module,
            data_adapter=self.adapter,
            managed_devices=self.managed_devices,
            threshold_rules=bad_rules
        )

        with patch.object(controller, '_to_serial') as mock_to_serial, \
             patch.object(controller, '_ok_to_send', return_value=True):

            controller._on_serial("!T:35#")
            mock_to_serial.assert_not_called()

    def test_update_threshold_rules(self):
        """Test updating threshold rules at runtime."""
        new_rules = {
            'humi': {
                'device': 'fan',
                'above': 70,
                'below': 60,
                'on_value': '1',
                'off_value': '0'
            }
        }

        self.controller.update_threshold_rules(new_rules)
        self.assertEqual(self.controller.get_threshold_rules(), new_rules)

        # Test new rule works
        with patch.object(self.controller, '_to_serial') as mock_to_serial, \
             patch.object(self.controller, '_ok_to_send', return_value=True):

            # Add humi to managed devices
            self.controller.managed_devices['humi'] = {
                'type': 'sensor', 'serial_abbr': 'H', 'is_switch': False
            }

            self.controller._on_serial("!H:75#")
            mock_to_serial.assert_called_once_with('fan', '1')


if __name__ == '__main__':
    unittest.main()