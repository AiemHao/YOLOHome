"""
YOLOHome Gateway - Entry Point
Main runner cho hệ thống gateway IoT
"""

import logging
import sys
import time
import os
import yaml
from typing import Optional

from Bridge import MQTTClient
from Adapter import DefaultDataAdapter
from Serial import SerialModule
from Controller import MainController

# ============================================================================
# CONFIGURATION LOADER
# ============================================================================

def load_config(config_path: str = None) -> dict:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to config.yml (default: ../config.yml relative to this file)
    
    Returns:
        Dictionary with mqtt, serial, app keys
    """
    if config_path is None:
        # Default: look for config.yml in parent directory of GateWay/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gateway_dir = os.path.dirname(current_dir)
        config_path = os.path.join(gateway_dir, 'config.yml')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    config = load_config()
    MQTT_CONFIG = config.get('mqtt', {})
    SERIAL_CONFIG = config.get('serial', {})
    APP_CONFIG = config.get('app', {})
    RATE_LIMIT_CONFIG = config.get('rate_limit', {})
    DEVICES_CONFIG = config.get('devices', {})
    MANAGED_DEVICES_CONFIG = config.get('managed_devices', {})
    AUTOMATION_CONFIG = config.get('automation', {})
    
    # Validate required sections
    if not MQTT_CONFIG:
        logger.error("Missing required config section: 'mqtt'")
        sys.exit(1)
    if not SERIAL_CONFIG:
        logger.error("Missing required config section: 'serial'")
        sys.exit(1)
    if not APP_CONFIG:
        logger.error("Missing required config section: 'app'")
        sys.exit(1)
        
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    sys.exit(1)

# ============================================================================
# GATEWAY CLASS
# ============================================================================

class YOLOHomeGateway:
    """
    Main Gateway class quản lý toàn bộ hệ thống
    """
    
    def __init__(
        self,
        mqtt_config: dict,
        serial_config: dict,
        app_config: dict = None,
        rate_limit_config: dict = None,
        device_config: dict = None,
        managed_devices_config: dict = None,
        automation_config: dict = None,
    ):
        """
        Khởi tạo Gateway
        
        Args:
            mqtt_config: MQTT configuration dict
            serial_config: Serial configuration dict
            app_config: Application configuration dict
            rate_limit_config: Rate limiting configuration dict
            device_config: Device mapping configuration dict
            managed_devices_config: Managed device metadata from config
            automation_config: Automation rules from config
        """
        self.mqtt_config = mqtt_config
        self.serial_config = serial_config
        self.app_config = app_config or {}
        self.rate_limit_config = rate_limit_config or {}
        self.device_config = device_config or {}
        self.managed_devices_config = managed_devices_config or {}
        self.automation_config = automation_config or {}
        
        # Extract MQTT topics configuration
        self.mqtt_topics = self.mqtt_config.get('topics', {})
        
        # Initialize modules
        self.mqtt_client: Optional[MQTTClient] = None
        self.serial_module: Optional[SerialModule] = None
        self.controller: Optional[MainController] = None
        self.adapter = None
        
        logger.info("="*60)
        logger.info("YOLOHome Gateway - Initializing...")
        logger.info("="*60)
    
    def setup(self) -> bool:
        """
        Thiết lập toàn bộ hệ thống
        
        Returns:
            True nếu setup thành công, False nếu lỗi
        """
        try:
            serial_online = True
            # 1. Setup Adapter
            logger.info("[1/4] Setting up Data Adapter...")
            # Get device mapping from config, or use default
            device_mapping = self.device_config if self.device_config else None
            topic_prefix = self.mqtt_topics.get('prefix', 'home')
            location = self.mqtt_topics.get('location', 'livingroom')
            self.adapter = DefaultDataAdapter(
                device_mapping=device_mapping,
                topic_prefix=topic_prefix,
                location=location,
            )
            logger.info(f"✓ Adapter: DefaultDataAdapter with {len(self.adapter.device_mapping)} devices")
            
            # 2. Setup Serial Module
            logger.info("[2/4] Setting up Serial Module...")
            try:
                self.serial_module = SerialModule(
                    port=self.serial_config['port'],
                    baudrate=self.serial_config.get('baudrate', 115200),
                    timeout=self.serial_config.get('timeout', 1)
                )
                logger.info(f"✓ Serial connected to {self.serial_config['port']}")
            except Exception as e:
                logger.warning(f"✗ Serial connection failed: {e}")
                logger.info("  Continuing without Serial (kit offline mode)...")
                self.serial_module = None
                serial_online = False
            
            # 3. Setup MQTT Client (defer start until callbacks are attached)
            logger.info("[3/4] Setting up MQTT Client...")
            self.mqtt_client = MQTTClient(
                host=self.mqtt_config.get('host', 'localhost'),
                port=self.mqtt_config.get('port', 1883),
                username=self.mqtt_config.get('username', ''),
                password=self.mqtt_config.get('password', ''),
                sub_topics=self.mqtt_config.get('subscribe_topics', []),
            )
            logger.info("✓ MQTT client configured")
            
            # 4. Setup Main Controller
            logger.info("[4/4] Setting up Main Controller...")
            if self.serial_module is None:
                # Nếu serial không có, dùng mock
                from unittest.mock import MagicMock
                self.serial_module = MagicMock()
                logger.info("  Using mock Serial module")
            
            # Extract AI configuration
            ai_config = self.automation_config.get('ai', {})
            ai_enabled = ai_config.get('enabled', False)
            ai_model_path = ai_config.get('model_path')

            threshold_config = self.automation_config.get('threshold', {})
            threshold_enabled = threshold_config.get('enabled', self.automation_config.get('enabled', True))
            
            self.controller = MainController(
                mqtt_client=self.mqtt_client,
                serial_module=self.serial_module,
                data_adapter=self.adapter,
                rate_limit_mqtt=self.rate_limit_config.get('mqtt_to_serial', 0.1),
                rate_limit_serial=self.rate_limit_config.get('serial_to_mqtt', 0.5),
                mqtt_topics=self.mqtt_topics,
                state_history_size=self.app_config.get('state_history_size', 20),
                managed_devices=self.managed_devices_config,
                threshold_rules=self.automation_config.get('thresholds', {}),
                ai_enabled=ai_enabled,
                ai_model_path=ai_model_path,
            )
            logger.debug(f"Loaded thresholds: {AUTOMATION_CONFIG.get('thresholds', {})}")
            logger.debug(f"AI config: enabled={ai_enabled}, model={ai_model_path}")

            # Set threshold enabled state from config (support new key threshold.enabled)
            self.controller.set_threshold_enabled(threshold_enabled)
            
            # Log automation status
            automation_status = self.controller.get_automation_status()
            logger.info(f"Automation: {automation_status['active_mode']} mode (Threshold: "
                       f"{automation_status['threshold']['enabled']}, "
                       f"AI: {automation_status['ai']['enabled']})")
            logger.info("✓ Main Controller initialized")

            # Start MQTT after controller callback registration.
            self.mqtt_client.start()
            logger.info("✓ MQTT client started")

            # Chờ MQTT connected
            time.sleep(1)
            
            # Bắt đầu serial background reading nếu có
            if serial_online and hasattr(self.serial_module, 'start_reading'):
                self.serial_module.start_reading()
                logger.info("✓ Serial background reading started")
            
            logger.info("="*60)
            logger.info("✓ Gateway setup completed successfully!")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"✗ Setup failed: {e}", exc_info=True)
            return False
    
    def run(self):
        """
        Chạy gateway main loop
        """
        if not self.controller:
            logger.error("Controller not initialized! Call setup() first.")
            return

        if self.controller.is_threshold_enabled():
            rules = self.controller.threshold_rules
            if rules:
                logger.info("Threshold automation is enabled. Loaded threshold rules:")
                for rule in rules:
                    sensor = rule.get('sensor', '<unknown>')
                    device = rule.get('device', '<unknown>')
                    above = rule.get('above')
                    below = rule.get('below')
                    on_value = rule.get('on_value')
                    off_value = rule.get('off_value')
                    conditions = []
                    if above is not None:
                        conditions.append(f"above={above}")
                    if below is not None:
                        conditions.append(f"below={below}")
                    condition_str = ", ".join(conditions) if conditions else "no condition"
                    logger.info(
                        f"  - sensor={sensor}, device={device}, {condition_str}, "
                        f"on={on_value}, off={off_value}"
                    )
            else:
                logger.info("Threshold automation enabled, but no threshold rules were loaded.")

        logger.info("Starting gateway main loop... (Press Ctrl+C to stop)")
        
        try:
            loop_interval = self.app_config.get('loop_interval', 0.1)
            
            while True:
                # Main loop tasks
                # Có thể thêm:
                # - Health checks
                # - Periodic tasks (sync states, etc.)
                # - Command queue processing
                # - Logging/monitoring
                
                time.sleep(loop_interval)
                
        except KeyboardInterrupt:
            logger.info("\nShutdown signal received (Ctrl+C)")
            self.shutdown()
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            self.shutdown()
    
    def shutdown(self):
        """Dừng gateway một cách an toàn"""
        logger.info("Shutting down gateway...")
        
        try:
            # Stop serial
            if self.serial_module and hasattr(self.serial_module, 'stop_reading'):
                self.serial_module.stop_reading()
                logger.info("✓ Serial stopped")
            
            if self.serial_module and hasattr(self.serial_module, 'disconnect'):
                self.serial_module.disconnect()
                logger.info("✓ Serial disconnected")
            
            # Stop MQTT
            if self.mqtt_client:
                self.mqtt_client.stop()
                logger.info("✓ MQTT stopped")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("="*60)
        logger.info("Gateway stopped.")
        logger.info("="*60)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    
    # Khởi tạo gateway
    gateway = YOLOHomeGateway(
        mqtt_config=MQTT_CONFIG,
        serial_config=SERIAL_CONFIG,
        app_config=APP_CONFIG,
        rate_limit_config=RATE_LIMIT_CONFIG,
        device_config=DEVICES_CONFIG,
        managed_devices_config=MANAGED_DEVICES_CONFIG,
        automation_config=AUTOMATION_CONFIG,
    )
    
    # Setup hệ thống
    if not gateway.setup():
        logger.error("Failed to setup gateway!")
        sys.exit(1)
    
    # Chạy main loop
    gateway.run()


if __name__ == "__main__":
    main()