"""AI-based automation service using Decision Tree model for device control.

Provides same interface as ThresholdService but uses trained ML model for decisions.
Supports both threshold-based and AI-based automation modes.
"""

import logging
import os
import pickle
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AIService:
    """Manages AI-based automation using Decision Tree model.
    
    Controls devices based on sensor values using a trained Decision Tree classifier.
    Can work with sunlight, temperature, and humidity sensors for curtain/servo control.
    """

    def __init__(self, model_path: str = None, enabled: bool = False):
        """Initialize AI service.

        Args:
            model_path: Path to trained Decision Tree model (pickle file).
                       If None, model will be lazy-loaded or generated.
            enabled: Whether AI automation is active.
        """
        self.model_path = model_path
        self.enabled = enabled
        self.model = None
        self.action_state: Dict[str, Any] = {}  # Track last sent action per device
        
        # Sensor requirements for model inference
        self.required_sensors = ['light', 'temp', 'humi']  # sunlight, temperature, humidity
        self.target_device = 'servo'  # Device this AI controls (curtain/servo)
        
        # Load model if path provided and file exists
        if model_path and os.path.exists(model_path):
            try:
                self._load_model(model_path)
                logger.info(f"✓ AI model loaded from {model_path}")
            except Exception as e:
                logger.warning(f"Failed to load AI model: {e}")
                self.model = None

    def _load_model(self, model_path: str) -> None:
        """Load trained Decision Tree model from pickle file.
        
        Args:
            model_path: Path to pickle file containing trained model.
            
        Raises:
            FileNotFoundError: If model file not found.
            Exception: If pickle loading fails.
        """
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"Model loaded successfully from {model_path}")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable AI automation."""
        self.enabled = enabled
        logger.info(f"AI automation {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        """Check if AI automation is enabled."""
        return self.enabled and self.model is not None

    def _validate_sensor_data(self, sensor_dict: Dict[str, float]) -> bool:
        """Validate that all required sensors have data.
        
        Args:
            sensor_dict: Dict with sensor names -> values.
            
        Returns:
            True if all required sensors present and numeric.
        """
        for sensor in self.required_sensors:
            if sensor not in sensor_dict:
                logger.debug(f"Missing sensor data: {sensor}")
                return False
            try:
                float(sensor_dict[sensor])
            except (ValueError, TypeError):
                logger.debug(f"Invalid sensor value for {sensor}: {sensor_dict[sensor]}")
                return False
        return True

    def predict_action(self, sensor_dict: Dict[str, float]) -> Optional[int]:
        """Predict device action using trained model.
        
        Args:
            sensor_dict: Dict with sensor values {
                'light': sunlight_percent (0-100),
                'temp': temperature (-10 to 50 °C),
                'humi': humidity_percent (0-100)
            }
            
        Returns:
            0 (close/off) or 1 (open/on), or None if prediction fails.
        """
        if not self.is_enabled():
            logger.debug("AI service disabled, cannot predict")
            return None

        if not self._validate_sensor_data(sensor_dict):
            logger.warning(f"Invalid sensor data for AI prediction: {sensor_dict}")
            return None

        try:
            # Extract features in correct order: [sunlight, temperature, humidity]
            features = [[
                float(sensor_dict['light']),   # sunlight_percent
                float(sensor_dict['temp']),    # temperature
                float(sensor_dict['humi']),    # humidity_percent
            ]]
            
            prediction = int(self.model.predict(features)[0])
            logger.debug(f"AI prediction: L={sensor_dict['light']:.1f} "
                        f"T={sensor_dict['temp']:.1f} H={sensor_dict['humi']:.1f} "
                        f"-> {prediction}")
            return prediction
            
        except Exception as e:
            logger.error(f"AI prediction error: {e}")
            return None

    def check_and_trigger(self, sensor_dict: Dict[str, float], 
                         send_command_callback) -> None:
        """Check sensors and trigger device action via AI model.
        
        Args:
            sensor_dict: Dict of sensor values.
            send_command_callback: Function(device_name, command_value) to execute action.
        """
        if not self.is_enabled():
            logger.debug("AI service disabled, skipping check")
            return

        action = self.predict_action(sensor_dict)
        if action is None:
            return

        # Check if we already sent this action (avoid duplicates)
        last_action = self.action_state.get(self.target_device)
        if last_action == action:
            logger.debug(f"Same AI action already sent to {self.target_device}, skipping")
            return

        self.action_state[self.target_device] = action
        
        action_str = "OPEN" if action == 1 else "CLOSE"
        logger.info(f"AI triggered: {self.target_device}={action} ({action_str}) "
                   f"(L={sensor_dict['light']:.1f} T={sensor_dict['temp']:.1f} "
                   f"H={sensor_dict['humi']:.1f})")
        
        send_command_callback(self.target_device, action)

    def get_status(self) -> Dict[str, Any]:
        """Get AI service status.
        
        Returns:
            Dict with enabled, model_loaded, and last_actions status.
        """
        return {
            'enabled': self.enabled,
            'model_loaded': self.model is not None,
            'model_path': self.model_path,
            'target_device': self.target_device,
            'active_actions': self.action_state.copy()
        }

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about trained model.
        
        Returns:
            Dict with model parameters, or None if no model loaded.
        """
        if self.model is None:
            return None

        try:
            info = {
                'type': self.model.__class__.__name__,
                'features': ['sunlight_percent', 'temperature', 'humidity_percent'],
                'output': ['close (0)', 'open (1)'],
            }
            
            # Add Decision Tree specific info
            if hasattr(self.model, 'max_depth'):
                info['max_depth'] = self.model.max_depth
            if hasattr(self.model, 'n_features_in_'):
                info['n_features'] = self.model.n_features_in_
            if hasattr(self.model, 'tree_'):
                info['tree_depth'] = self.model.tree_.max_depth
                info['n_leaves'] = self.model.get_n_leaves()
                
            return info
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return None

    @staticmethod
    def train_and_save_model(training_script_path: str, output_model_path: str) -> bool:
        """Train model using provided script and save pickle.
        
        This is a helper method to generate trained model from scratch.
        The training_script_path should be the curtain_control_system.py path.
        
        Args:
            training_script_path: Path to training script (curtain_control_system.py).
            output_model_path: Where to save trained model pickle file.
            
        Returns:
            True if training succeeded, False otherwise.
        """
        try:
            logger.info(f"Training AI model from {training_script_path}...")
            
            # Dynamically import training script
            import importlib.util
            spec = importlib.util.spec_from_file_location("curtain_system", training_script_path)
            curtain_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(curtain_module)
            
            # Generate data and train
            generator = curtain_module.CurtainDataGenerator(seed=42)
            trainer = curtain_module.CurtainModelTrainer()
            
            train_file = "temp_train.csv"
            test_file = "temp_test.csv"
            
            generator.generate_dataset(n_samples=10000, output_file=train_file)
            generator.generate_dataset(n_samples=2000, output_file=test_file)
            
            trainer.train(train_file)
            accuracy = trainer.evaluate()
            
            # Save model
            os.makedirs(os.path.dirname(output_model_path) or '.', exist_ok=True)
            with open(output_model_path, 'wb') as f:
                pickle.dump(trainer.model, f)
            
            # Cleanup temp files
            try:
                os.remove(train_file)
                os.remove(test_file)
            except:
                pass
            
            logger.info(f"✓ Model trained and saved to {output_model_path} "
                       f"(Accuracy: {accuracy*100:.2f}%)")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return False
