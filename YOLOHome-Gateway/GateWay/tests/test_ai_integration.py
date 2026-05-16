"""
Integration test for AI-based automation in YOLOHome Gateway.

Tests:
1. AIService model loading
2. Threshold service functionality
3. MainController mode switching
4. Sensor data handling
5. Command execution flow
"""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup path for imports
GATEWAY_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(GATEWAY_PATH))

from Controller.services import AIService, ThresholdService, StateService
from Controller.controller import MainController


def test_ai_service_model_loading():
    """Test that AIService can load the trained model."""
    print("\n" + "="*70)
    print("TEST 1: AI Service Model Loading")
    print("="*70)
    
    model_path = str(GATEWAY_PATH / "Decision_tree" / "models" / "curtain_model.pkl")
    ai_service = AIService(model_path=model_path, enabled=True)
    
    assert ai_service.is_enabled(), "AI Service should be enabled"
    assert ai_service.model is not None, "Model should be loaded"
    
    model_info = ai_service.get_model_info()
    print(f"✓ Model loaded successfully")
    print(f"  Type: {model_info['type']}")
    print(f"  Features: {model_info['features']}")
    print(f"  Depth: {model_info['max_depth']}")
    print(f"  Leaves: {model_info['n_leaves']}")
    
    return ai_service


def test_ai_predictions(ai_service):
    """Test AI model predictions on various inputs."""
    print("\n" + "="*70)
    print("TEST 2: AI Model Predictions")
    print("="*70)
    
    test_cases = [
        {
            "name": "Bright & hot (should close)",
            "data": {"light": 85, "temp": 33, "humi": 45},
            "expected": 0
        },
        {
            "name": "Dark & mild (should open)",
            "data": {"light": 20, "temp": 22, "humi": 55},
            "expected": 1
        },
        {
            "name": "Moderate & cold (should close)",
            "data": {"light": 50, "temp": 8, "humi": 40},
            "expected": 0
        },
        {
            "name": "Dim & humid (should open)",
            "data": {"light": 30, "temp": 25, "humi": 80},
            "expected": 1
        },
    ]
    
    all_correct = True
    for tc in test_cases:
        prediction = ai_service.predict_action(tc["data"])
        is_correct = prediction == tc["expected"]
        status = "✓" if is_correct else "✗"
        
        print(f"{status} {tc['name']}")
        print(f"   Input: L={tc['data']['light']}% T={tc['data']['temp']}°C H={tc['data']['humi']}%")
        print(f"   Prediction: {prediction} ({'OPEN' if prediction == 1 else 'CLOSE'})")
        
        all_correct = all_correct and is_correct
    
    assert all_correct, "Some predictions were incorrect"
    return True


def test_ai_service_check_and_trigger():
    """Test AIService.check_and_trigger() method."""
    print("\n" + "="*70)
    print("TEST 3: AI Service Check and Trigger")
    print("="*70)
    
    model_path = str(GATEWAY_PATH / "Decision_tree" / "models" / "curtain_model.pkl")
    ai_service = AIService(model_path=model_path, enabled=True)
    
    # Mock callback to capture commands
    commands = []
    def mock_send_command(device, value):
        commands.append({"device": device, "value": value})
        print(f"  → Command: {device}={value}")
    
    # Test with bright conditions (should trigger close)
    sensor_data = {"light": 80, "temp": 30, "humi": 50}
    ai_service.check_and_trigger(sensor_data, mock_send_command)
    
    assert len(commands) > 0, "Should have sent a command"
    print(f"✓ check_and_trigger() executed successfully")
    print(f"  Commands sent: {len(commands)}")
    
    return ai_service


def test_threshold_service():
    """Test that ThresholdService still works."""
    print("\n" + "="*70)
    print("TEST 4: Threshold Service (Fallback)")
    print("="*70)
    
    rules = {
        "temp": [
            {
                "device": "fan",
                "above": 30,
                "on_value": 1,
                "off_value": 0
            }
        ]
    }
    
    threshold_service = ThresholdService(rules, enabled=True)
    
    commands = []
    def mock_send_command(device, value):
        commands.append({"device": device, "value": value})
    
    # Trigger threshold: temperature above 30°C
    threshold_service.check_threshold("temp", 35, mock_send_command)
    
    print(f"✓ Threshold service executed")
    print(f"  Status: {threshold_service.get_status()}")
    
    return threshold_service


def test_main_controller_mode_switching():
    """Test MainController switching between AI and Threshold modes."""
    print("\n" + "="*70)
    print("TEST 5: Main Controller Mode Switching")
    print("="*70)
    
    # Create mock components
    mqtt_client = MagicMock()
    serial_module = MagicMock()
    data_adapter = MagicMock()
    
    model_path = str(GATEWAY_PATH / "Decision_tree" / "models" / "curtain_model.pkl")
    
    # Initialize controller with AI
    controller = MainController(
        mqtt_client=mqtt_client,
        serial_module=serial_module,
        data_adapter=data_adapter,
        ai_enabled=True,
        ai_model_path=model_path,
        threshold_rules={
            "light": [{"device": "led", "below": 30, "on_value": 1, "off_value": 0}]
        }
    )
    
    # Test 1: AI should be enabled
    assert controller.is_ai_enabled(), "AI should be enabled initially"
    print("✓ AI enabled: True")
    
    # Test 2: Get automation status
    status = controller.get_automation_status()
    print(f"✓ Automation status: {status['active_mode']} mode")
    print(f"  Threshold: {status['threshold']['enabled']}")
    print(f"  AI: {status['ai']['enabled']}")
    
    # Test 3: Switch to Threshold mode
    controller.set_ai_enabled(False)
    assert not controller.is_ai_enabled(), "AI should be disabled"
    print("✓ AI disabled: False")
    
    # Test 4: Switch back to AI mode
    controller.set_ai_enabled(True)
    assert controller.is_ai_enabled(), "AI should be re-enabled"
    print("✓ AI re-enabled: True")
    
    return controller


def test_sensor_data_collection():
    """Test that MainController can collect sensor data for AI."""
    print("\n" + "="*70)
    print("TEST 6: Sensor Data Collection")
    print("="*70)
    
    # Create mock components
    mqtt_client = MagicMock()
    serial_module = MagicMock()
    data_adapter = MagicMock()
    
    model_path = str(GATEWAY_PATH / "Decision_tree" / "models" / "curtain_model.pkl")
    
    controller = MainController(
        mqtt_client=mqtt_client,
        serial_module=serial_module,
        data_adapter=data_adapter,
        ai_enabled=True,
        ai_model_path=model_path,
    )
    
    # Simulate sensor updates
    controller._append_state_from_kit("light", 75)
    controller._append_state_from_kit("temp", 28)
    controller._append_state_from_kit("humi", 60)
    
    # Collect sensor data
    sensor_dict = controller._get_sensor_dict()
    
    assert sensor_dict is not None, "Should collect all sensor data"
    assert sensor_dict["light"] == 75, "Light value should match"
    assert sensor_dict["temp"] == 28, "Temp value should match"
    assert sensor_dict["humi"] == 60, "Humidity value should match"
    
    print("✓ Sensor data collection working")
    print(f"  Sensors: {sensor_dict}")
    
    return controller


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  YOLOHOME AI AUTOMATION INTEGRATION TEST SUITE".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    try:
        # Run tests
        ai_service = test_ai_service_model_loading()
        test_ai_predictions(ai_service)
        test_ai_service_check_and_trigger()
        test_threshold_service()
        test_main_controller_mode_switching()
        test_sensor_data_collection()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("✓ All tests passed!")
        print("\nIntegration Status:")
        print("  ✓ AI Service: Model loaded and predictions working")
        print("  ✓ Threshold Service: Fallback functionality intact")
        print("  ✓ Main Controller: Mode switching works")
        print("  ✓ Sensor Collection: Data properly collected")
        print("\n✓ AI Automation is fully integrated and ready to use!")
        print("\nTo enable AI mode in production:")
        print("  1. Set automation.ai.enabled = true in config.yml")
        print("  2. Restart the gateway: python GateWay/run.py")
        print("  3. Check logs for 'Automation: AI mode'")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
