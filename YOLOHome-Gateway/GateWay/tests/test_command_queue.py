"""Test command queue for sequential threshold-triggered sends.

When multiple devices are triggered by threshold at same time, commands
should be queued and sent sequentially with mqtt_to_serial interval.
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from Controller.controller import MainController
from Adapter.default_adapter import DefaultDataAdapter


class TestCommandQueue(unittest.TestCase):
    """Test command queue functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mqtt_mock = MagicMock()
        self.serial_mock = MagicMock()
        
        # Device mapping for adapter
        self.device_mapping = {
            'temp': 'T',
            'humi': 'H',
            'light': 'Lu',
            'fan': 'F',
            'led': 'L',
            'servo': 'S',
        }
        
        self.adapter = DefaultDataAdapter(self.device_mapping)
        
        # Threshold rules triggering multiple devices
        self.threshold_rules = {
            'temp': [
                {'sensor': 'temp', 'device': 'fan', 'condition': '>', 'value': 30, 'on_value': '1', 'off_value': '0'},
                {'sensor': 'temp', 'device': 'led', 'condition': '>', 'value': 30, 'on_value': '1', 'off_value': '0'},
            ]
        }
        
        self.controller = MainController(
            mqtt_client=self.mqtt_mock,
            serial_module=self.serial_mock,
            data_adapter=self.adapter,
            rate_limit_mqtt=0.05,  # Small interval for testing
            rate_limit_serial=0.5,
            managed_devices={'temp': {}, 'humi': {}, 'light': {}, 'fan': {}, 'led': {}, 'servo': {}},
            threshold_rules=self.threshold_rules,
        )
    
    def test_queue_multiple_commands(self):
        """Test that multiple threshold triggers are queued."""
        self.controller.serial_mock = MagicMock()
        
        # Trigger threshold that should activate fan and led
        with patch.object(self.controller, '_to_serial') as mock_to_serial:
            self.controller._on_serial("!T:35#")
            
            # Wait for queue to process (should queue 2 commands)
            time.sleep(0.2)  # Allow time for async processing
            
            # Check that both devices were sent
            self.assertEqual(mock_to_serial.call_count, 2)
            
            # Get the calls to verify both fan and led were sent
            calls = mock_to_serial.call_args_list
            devices_sent = [call[0][0] for call in calls]
            self.assertIn('fan', devices_sent)
            self.assertIn('led', devices_sent)
            
            print(f"✓ Queued {mock_to_serial.call_count} commands for multiple devices")
    
    def test_queue_sequential_timing(self):
        """Test that queued commands are sent with rate limit interval between them."""
        rate_limit = 0.05  # 50ms
        self.controller.rate_limit_mqtt = rate_limit
        
        with patch.object(self.controller, '_to_serial') as mock_to_serial:
            # Enqueue 3 commands quickly
            self.controller._enqueue_command('fan', '1')
            self.controller._enqueue_command('led', '1')
            self.controller._enqueue_command('servo', '1')
            
            # All 3 should be queued
            self.assertEqual(len(self.controller.pending_commands), 3)
            
            # Wait for processing: 3 commands * 50ms interval = ~150ms
            start_time = time.time()
            time.sleep(0.2)
            elapsed = time.time() - start_time
            
            # Verify all were sent
            self.assertEqual(mock_to_serial.call_count, 3)
            
            # Timing should be roughly 3 * interval (with some tolerance)
            # Each send takes interval time before next
            expected_min_time = (3 - 1) * rate_limit  # 2 intervals for 3 items
            self.assertGreater(elapsed, expected_min_time - 0.02)  # Allow 20ms tolerance
            
            print(f"✓ Sequential sends: {mock_to_serial.call_count} commands in {elapsed:.3f}s")
    
    def test_queue_cleanup(self):
        """Test that cleanup stops queue processor."""
        # Enqueue some commands
        self.controller._enqueue_command('fan', '1')
        self.controller._enqueue_command('led', '1')
        
        # Queue processor should be running
        self.assertTrue(self.controller.queue_processor_running)
        
        # Clean up
        self.controller.cleanup()
        
        # Thread should be stopped
        self.assertFalse(self.controller.queue_processor_running)
        
        print("✓ Queue processor cleaned up successfully")


if __name__ == '__main__':
    unittest.main()
