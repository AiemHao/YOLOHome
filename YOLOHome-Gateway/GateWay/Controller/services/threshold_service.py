"""Threshold automation service for MainController."""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ThresholdService:
    """Manages internal threshold-based automation rules for multiple devices.
    
    Supports the configuration format:
    ```yaml
    automation:
      enabled: true
      thresholds:
        temp:                    # sensor name
          - device: fan          # target device
            above: 30            # trigger when > 30
            on_value: 1          # send this when condition met
            off_value: 0         # send this when condition not met
        humi:
          - device: led
            above: 70
            below: 65            # both above AND below (range: 65 < value < 70 = off, else on)
            on_value: 0
            off_value: 1
          - device: servo        # multiple rules per sensor
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

    def __init__(self, threshold_config: Dict[str, Any] = None, enabled: bool = True):
        """Initialize threshold service.

        Args:
            threshold_config: Dict mapping sensor names to list of device rules.
                            Format: {"sensor_name": [{"device": "...", "above": X, ...}, ...]}
            enabled: Whether threshold automation is active.
        """
        self.threshold_config = threshold_config or {}
        self.enabled = enabled
        self.action_state: Dict[str, Any] = {}  # Track last sent action per device
        self._parse_config()

    def _parse_config(self) -> None:
        """Parse threshold configuration into a list of (sensor, device_rule) tuples."""
        self.rules = []  # List of (sensor_name, device_name, rule_dict)
        
        if not self.threshold_config or not isinstance(self.threshold_config, dict):
            logger.debug("No threshold configuration provided")
            return
        
        for sensor_name, device_rules in self.threshold_config.items():
            if not isinstance(device_rules, list):
                logger.warning(f"Threshold for '{sensor_name}' is not a list, skipping")
                continue
            
            for device_rule in device_rules:
                if not isinstance(device_rule, dict):
                    logger.warning(f"Rule for '{sensor_name}' is not a dict, skipping")
                    continue
                
                device_name = device_rule.get('device', '').strip().lower()
                if not device_name:
                    logger.warning(f"Rule for '{sensor_name}' missing 'device' field")
                    continue
                
                self.rules.append({
                    'sensor': sensor_name.strip().lower(),
                    'device': device_name,
                    'above': self._parse_numeric(device_rule.get('above')),
                    'below': self._parse_numeric(device_rule.get('below')),
                    'on_value': device_rule.get('on_value'),
                    'off_value': device_rule.get('off_value'),
                })
            
            logger.debug(f"Parsed {len(device_rules)} rule(s) for sensor '{sensor_name}'")

    @staticmethod
    def _parse_numeric(value: Any) -> Optional[float]:
        """Parse numeric threshold value."""
        if value is None:
            return None
        try:
            return float(str(value).strip())
        except (ValueError, AttributeError):
            return None

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable threshold automation."""
        self.enabled = enabled
        logger.info(f"Threshold automation {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        """Check if threshold automation is enabled."""
        return self.enabled

    def _condition_met(self, sensor_value: float, rule: Dict[str, Any]) -> bool:
        """Check if sensor value meets the threshold condition in a rule.
        
        Args:
            sensor_value: Current sensor reading
            rule: Rule dict with 'above', 'below' fields
        
        Returns:
            True if condition is met, False otherwise
            
        Logic:
        - If only 'above' specified: condition = value > above
        - If only 'below' specified: condition = value < below  
        - If both specified: condition = (value > above) OR (value < below)
                            i.e., outside the range [below, above]
        """
        above = rule.get('above')
        below = rule.get('below')
        
        # Both specified: outside the range (hysteresis)
        if above is not None and below is not None:
            return sensor_value > above or sensor_value < below
        
        # Only above
        if above is not None:
            return sensor_value > above
        
        # Only below
        if below is not None:
            return sensor_value < below
        
        # No condition specified
        logger.warning(f"Rule has no threshold conditions: {rule}")
        return False

    def check_threshold(self, sensor_name: str, value: Any, send_command_callback) -> None:
        """Check threshold rules for a sensor and trigger actions if needed.

        Args:
            sensor_name: Sensor device name.
            value: Current sensor value.
            send_command_callback: Function(device_name, command_value) to send command.
        """
        if not self.enabled:
            logger.debug(f"Service disabled, skipping threshold check for {sensor_name}")
            return

        sensor_name_lower = str(sensor_name).strip().lower()
        
        try:
            sensor_value = float(str(value).strip())
        except (ValueError, AttributeError):
            logger.warning(f"Threshold check skipped: non-numeric value for {sensor_name}: {value}")
            return

        # Check all rules for this sensor
        matching_rules = [r for r in self.rules if r['sensor'] == sensor_name_lower]
        
        if not matching_rules:
            logger.debug(f"No threshold rules found for sensor '{sensor_name}'")
            return

        for rule in matching_rules:
            device_name = rule['device']
            condition_met = self._condition_met(sensor_value, rule)
            command_value = rule['on_value'] if condition_met else rule['off_value']
            
            # Check if we already sent this command to avoid duplicates
            last_sent = self.action_state.get(device_name)
            if last_sent == command_value:
                logger.debug(
                    f"Same command already sent to {device_name}, skipping "
                    f"(sensor={sensor_name}, value={sensor_value}, cmd={command_value})"
                )
                continue
            
            self.action_state[device_name] = command_value
            
            logger.info(
                f"Threshold triggered: {sensor_name}={sensor_value} "
                f"-> {device_name}={command_value} "
                f"(on={rule['on_value']}, off={rule['off_value']})"
            )
            
            send_command_callback(device_name, command_value)

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get current threshold rules as normalized dicts."""
        return [r.copy() for r in self.rules]

    def update_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Update threshold rules from raw list format.
        
        Args:
            rules: List of rule dicts.
        """
        self.rules = rules or []
        logger.info(f"Updated threshold rules: {len(self.rules)} rules")

    def add_rule(self, rule: Dict[str, Any]) -> None:
        """Add a single threshold rule.
        
        Args:
            rule: Rule dict to add.
        """
        self.rules.append(rule)
        logger.info(f"Added rule: {rule}")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by device name.
        
        Args:
            rule_id: Device name to remove rules for.
            
        Returns:
            True if rules were removed, False if none found.
        """
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.get('device') != rule_id]
        if len(self.rules) < original_count:
            logger.info(f"Removed rules for device {rule_id}")
            return True
        return False

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get first rule for a device.
        
        Args:
            rule_id: Device name.
            
        Returns:
            Rule dict if found, None otherwise.
        """
        for rule in self.rules:
            if rule.get('device') == rule_id:
                return rule.copy()
        return None

    def update_rule(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """Update an existing rule by device name.
        
        Args:
            rule_id: Device name to update.
            rule: Updated rule dict.
            
        Returns:
            True if rule was updated, False if not found.
        """
        for i, r in enumerate(self.rules):
            if r.get('device') == rule_id:
                self.rules[i] = rule
                logger.info(f"Updated rule for device {rule_id}")
                return True
        return False

    def get_rules_for_sensor(self, sensor_name: str) -> List[Dict[str, Any]]:
        """Get all rules for a specific sensor.
        
        Args:
            sensor_name: Sensor name to query.
            
        Returns:
            List of rules for this sensor.
        """
        sensor_name_lower = str(sensor_name).strip().lower()
        return [r.copy() for r in self.rules if r.get('sensor') == sensor_name_lower]

    def get_status(self) -> Dict[str, Any]:
        """Get threshold service status.
        
        Returns:
            Dict containing enabled status, rule count, and active actions.
        """
        return {
            'enabled': self.enabled,
            'rules_count': len(self.rules),
            'active_actions': self.action_state.copy()
        }

#       humi:                        # multi rule (list) - một sensor, nhiều device
#         - high: 70
#           action_device: led
#           action_value: "0"
#           enabled: true
#         - high: 80
#           action_device: servo
#           action_value: "0"
#           enabled: true
#     """

#     def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
#         """Initialize threshold service.

#         Args:
#             thresholds: Dict of sensor thresholds from config.yml.
#                 Value có thể là dict (single rule) hoặc list (multi rule).
#         """
#         # Chuẩn hoá tất cả về list để xử lý đồng nhất
#         self.thresholds: Dict[str, List[Dict[str, Any]]] = {}
#         self._load(thresholds or {})
#         logger.info(f"ThresholdService init | sensors: {list(self.thresholds.keys())}")

#     def _load(self, thresholds: Dict[str, Any]) -> None:
#         """Chuẩn hoá single rule (dict) và multi rule (list) về cùng format."""
#         normalized: Dict[str, List[Dict[str, Any]]] = {}
#         for sensor, rule in thresholds.items():
#             if isinstance(rule, list):
#                 rules = rule
#             else:
#                 rules = [rule]
#             # Đảm bảo mỗi rule có enabled flag
#             for r in rules:
#                 if 'enabled' not in r:
#                     r['enabled'] = True
#             normalized[sensor.lower()] = rules
#         self.thresholds = normalized

#     def check_and_trigger(
#         self,
#         device_name: str,
#         value: Any,
#         send_callback,
#         get_current_state=None,
#     ) -> None:
#         """Check threshold và trigger action nếu cần.

#         Args:
#             device_name: Tên sensor (ví dụ: 'temp', 'humi').
#             value: Giá trị hiện tại của sensor.
#             send_callback: Hàm gửi lệnh, signature: (device, value) -> bool
#             get_current_state: Hàm lấy state hiện tại, signature: (device) -> Any
#         """
#         rules = self.thresholds.get(str(device_name).lower())
#         if not rules:
#             return

#         try:
#             numeric_value = float(value)
#         except (ValueError, TypeError):
#             logger.debug(f"Non-numeric value for {device_name}: {value}")
#             return

#         for rule in rules:
#             self._apply_rule(device_name, numeric_value, rule, send_callback, get_current_state)

#     def _apply_rule(
#         self,
#         sensor_name: str,
#         numeric_value: float,
#         rule: Dict[str, Any],
#         send_callback,
#         get_current_state,
#     ) -> None:
#         if not rule.get('enabled', True):
#             logger.debug(f"Threshold rule disabled for {sensor_name} → {rule.get('action_device')}")
#             return

#         action_device = rule.get('action_device', '')
#         if not action_device:
#             return

#         action_needed = False
#         if 'high' in rule and numeric_value > float(rule['high']):
#             action_needed = True
#             logger.info(f"Threshold exceeded: {sensor_name}={numeric_value} > {rule['high']}")
#         elif 'low' in rule and numeric_value < float(rule['low']):
#             action_needed = True
#             logger.info(f"Threshold exceeded: {sensor_name}={numeric_value} < {rule['low']}")

#         if not action_needed:
#             return

#         action_value = str(rule.get('action_value', '1'))

#         # Bỏ qua nếu device đã ở đúng trạng thái
#         if get_current_state:
#             current = get_current_state(action_device)
#             if str(current) == action_value:
#                 logger.debug(f"Threshold skipped: {action_device} already at {action_value}")
#                 return

#         logger.info(f"Triggering: {action_device} = {action_value}")
#         send_callback(action_device, action_value)