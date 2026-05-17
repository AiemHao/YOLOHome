"""Test cases for ThresholdService."""

import unittest
import sys
import os
from unittest.mock import MagicMock, call

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Controller.services.threshold_service import ThresholdService


class TestThresholdService(unittest.TestCase):
    """Test cases for ThresholdService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.rules = [
            {
                "id": "rule_1",
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
                "id": "rule_2",
                "enabled": True,
                "sensors": ["temperature"],
                "conditions": {
                    "type": "below",
                    "value": 20
                },
                "actions": [
                    {"device": "heater", "command": "on"}
                ]
            },
            {
                "id": "rule_3",
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
        self.service = ThresholdService(self.rules, enabled=True)

    def test_initialization(self):
        """Test service initialization."""
        self.assertTrue(self.service.is_enabled())
        self.assertEqual(len(self.service.get_rules()), 3)
        self.assertEqual(self.service.action_state, {})

    def test_set_enabled(self):
        """Test enabling/disabling threshold automation."""
        self.service.set_enabled(False)
        self.assertFalse(self.service.is_enabled())

        self.service.set_enabled(True)
        self.assertTrue(self.service.is_enabled())

    def test_single_sensor_multiple_actions(self):
        """Test one sensor triggering multiple actions on different devices."""
        mock_callback = MagicMock()

        # Temperature > 30 should trigger both fan and ac
        self.service.check_threshold('temperature', '32', mock_callback)
        
        # Should be called twice - once for fan, once for ac
        self.assertEqual(mock_callback.call_count, 2)
        calls = [call('fan', 'on'), call('ac', 'cool')]
        mock_callback.assert_has_calls(calls, any_order=True)

    def test_multiple_sensors_same_device(self):
        """Test multiple sensors can control the same device."""
        mock_callback = MagicMock()

        # First trigger rule_1 (temperature > 30 -> fan on)
        self.service.check_threshold('temperature', '32', mock_callback)
        self.assertEqual(mock_callback.call_count, 2)  # fan and ac

        mock_callback.reset_mock()

        # Then trigger rule_3 (humidity > 70 -> dehumidifier on)
        self.service.check_threshold('humidity', '75', mock_callback)
        self.assertEqual(mock_callback.call_count, 1)  # dehumidifier

    def test_temperature_above_threshold(self):
        """Test temperature above threshold triggers correct action."""
        mock_callback = MagicMock()

        self.service.check_threshold('temperature', '35', mock_callback)
        self.assertEqual(mock_callback.call_count, 2)
        
        mock_callback.reset_mock()

        # Same value should not trigger again (already sent)
        self.service.check_threshold('temperature', '35', mock_callback)
        mock_callback.assert_not_called()

    def test_temperature_below_threshold(self):
        """Test temperature below threshold triggers heater."""
        mock_callback = MagicMock()

        self.service.check_threshold('temperature', '18', mock_callback)
        mock_callback.assert_called_once_with('heater', 'on')

    def test_threshold_no_trigger_in_range(self):
        """Test threshold does not trigger when value is in range."""
        mock_callback = MagicMock()

        # Temperature = 25 (between 20-30) should not trigger
        self.service.check_threshold('temperature', '25', mock_callback)
        mock_callback.assert_not_called()

    def test_threshold_disabled_service(self):
        """Test threshold does not trigger when service is disabled."""
        self.service.set_enabled(False)
        mock_callback = MagicMock()

        self.service.check_threshold('temperature', '35', mock_callback)
        mock_callback.assert_not_called()

    def test_disabled_rule(self):
        """Test disabled rule does not trigger."""
        mock_callback = MagicMock()
        
        # Disable rule_1
        self.rules[0]['enabled'] = False
        self.service.update_rules(self.rules)

        # temperature > 30 should not trigger disabled rule
        self.service.check_threshold('temperature', '35', mock_callback)
        mock_callback.assert_not_called()

    def test_invalid_sensor_value(self):
        """Test threshold handles invalid sensor values gracefully."""
        mock_callback = MagicMock()

        # Non-numeric value should not trigger
        self.service.check_threshold('temperature', 'invalid', mock_callback)
        mock_callback.assert_not_called()

        # Empty value should not trigger
        self.service.check_threshold('temperature', '', mock_callback)
        mock_callback.assert_not_called()

    def test_unknown_sensor(self):
        """Test threshold does not trigger for unknown sensors."""
        mock_callback = MagicMock()

        self.service.check_threshold('unknown_sensor', '35', mock_callback)
        mock_callback.assert_not_called()

    def test_range_condition(self):
        """Test range condition type."""
        rules_range = [
            {
                "id": "range_rule",
                "enabled": True,
                "sensors": ["light"],
                "conditions": {
                    "type": "range",
                    "value": 100,
                    "value_high": 500
                },
                "actions": [
                    {"device": "lamp", "command": "on"}
                ]
            }
        ]
        service = ThresholdService(rules_range)
        mock_callback = MagicMock()

        # Value in range should trigger
        service.check_threshold('light', '300', mock_callback)
        mock_callback.assert_called_once_with('lamp', 'on')

        mock_callback.reset_mock()

        # Value below range should not trigger
        service.check_threshold('light', '50', mock_callback)
        mock_callback.assert_not_called()

        # Value above range should not trigger
        service.check_threshold('light', '600', mock_callback)
        mock_callback.assert_not_called()

    def test_equals_condition(self):
        """Test equals condition type."""
        rules_equals = [
            {
                "id": "equals_rule",
                "enabled": True,
                "sensors": ["door"],
                "conditions": {
                    "type": "equals",
                    "value": 1
                },
                "actions": [
                    {"device": "alarm", "command": "on"}
                ]
            }
        ]
        service = ThresholdService(rules_equals)
        mock_callback = MagicMock()

        # Value equals 1 should trigger
        service.check_threshold('door', '1', mock_callback)
        mock_callback.assert_called_once_with('alarm', 'on')

        mock_callback.reset_mock()

        # Value not equals should not trigger
        service.check_threshold('door', '0', mock_callback)
        mock_callback.assert_not_called()

    def test_update_rules(self):
        """Test updating threshold rules."""
        new_rules = [
            {
                "id": "new_rule",
                "enabled": True,
                "sensors": ["light"],
                "conditions": {
                    "type": "above",
                    "value": 500
                },
                "actions": [
                    {"device": "led", "command": "bright"}
                ]
            }
        ]

        self.service.update_rules(new_rules)
        self.assertEqual(len(self.service.get_rules()), 1)
        self.assertEqual(self.service.get_rules()[0]['id'], 'new_rule')

    def test_add_rule(self):
        """Test adding a single rule."""
        new_rule = {
            "id": "new_rule",
            "enabled": True,
            "sensors": ["pressure"],
            "conditions": {
                "type": "above",
                "value": 1000
            },
            "actions": [
                {"device": "valve", "command": "close"}
            ]
        }

        self.service.add_rule(new_rule)
        self.assertEqual(len(self.service.get_rules()), 4)

    def test_remove_rule(self):
        """Test removing a rule by ID."""
        success = self.service.remove_rule('rule_1')
        self.assertTrue(success)
        self.assertEqual(len(self.service.get_rules()), 2)

        # Try removing non-existent rule
        success = self.service.remove_rule('non_existent')
        self.assertFalse(success)

    def test_get_rule_by_id(self):
        """Test retrieving a rule by ID."""
        rule = self.service.get_rule_by_id('rule_1')
        self.assertIsNotNone(rule)
        self.assertEqual(rule['id'], 'rule_1')

        # Try getting non-existent rule
        rule = self.service.get_rule_by_id('non_existent')
        self.assertIsNone(rule)

    def test_update_rule(self):
        """Test updating an existing rule."""
        updated_rule = {
            "id": "rule_1",
            "enabled": True,
            "sensors": ["temperature"],
            "conditions": {
                "type": "above",
                "value": 40
            },
            "actions": [
                {"device": "ac", "command": "max_cool"}
            ]
        }

        success = self.service.update_rule('rule_1', updated_rule)
        self.assertTrue(success)
        
        rule = self.service.get_rule_by_id('rule_1')
        self.assertEqual(rule['conditions']['value'], 40)

    def test_get_rules_for_sensor(self):
        """Test getting all rules for a specific sensor."""
        rules = self.service.get_rules_for_sensor('temperature')
        self.assertEqual(len(rules), 2)
        rule_ids = [r['id'] for r in rules]
        self.assertIn('rule_1', rule_ids)
        self.assertIn('rule_2', rule_ids)

        # Test for sensor with single rule
        rules = self.service.get_rules_for_sensor('humidity')
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]['id'], 'rule_3')

        # Test for sensor with no rules
        rules = self.service.get_rules_for_sensor('unknown')
        self.assertEqual(len(rules), 0)
        self.assertEqual(mock_callback.call_args, call('fan', '1'))


if __name__ == '__main__':
    unittest.main()