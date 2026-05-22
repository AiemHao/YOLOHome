"""Main bus for MQTT ↔ Serial message routing.

Routes messages between MQTT broker and Serial device, applies rate limiting,
and maintains device state cache.
"""

import logging
import json
import re
import threading
import time
from queue import Queue, Empty
from typing import Dict, Any, Optional, List
from datetime import datetime
from .services import DeviceService, StateService, ThresholdService, AIService

logger = logging.getLogger(__name__)


class MainController:
    """Central message router between MQTT and Serial channels.
    
    Handles bidirectional message translation, rate limiting, device state
    caching, and command processing (getall, device queries).
    """
    
    def __init__(self, mqtt_client, serial_module, data_adapter, 
                 rate_limit_mqtt: float = 0.1, rate_limit_serial: float = 0.5,
                 mqtt_topics: Dict[str, str] = None,
                 state_history_size: int = 20,
                 managed_devices: Dict[str, Dict[str, Any]] = None,
                 threshold_rules: List[Dict[str, Any]] = None,
                 ai_enabled: bool = False,
                 ai_model_path: str = None,
                 batch_mode: bool = True,
                 inter_command_delay: float = 0.005):
        """Initialize the message router.
        
        Args:
            mqtt_client: MQTT broker interface instance.
            serial_module: Serial device interface instance.
            data_adapter: Format translator (MQTT ↔ Serial ↔ JSON).
            rate_limit_mqtt: Minimum interval in seconds between MQTT→Serial messages.
            rate_limit_serial: Minimum interval in seconds between Serial→MQTT messages.
            mqtt_topics: Topic configuration dict with keys: getall, state_prefix, state_all.
            threshold_rules: List of internal automation threshold rules.
            ai_enabled: Whether to use AI-based automation instead of threshold rules.
            ai_model_path: Path to trained Decision Tree model pickle file.
        """
        self.mqtt = mqtt_client
        self.serial = serial_module
        self.adapter = data_adapter
        
        self.mqtt_topics = mqtt_topics or {}
        self.topic_system_getall = self.mqtt_topics.get('system_getall', 'home/system/getall')
        self.topic_system_state_all = self.mqtt_topics.get('system_state_all', 'home/system/stateall')
        self.device_service = DeviceService(self.adapter, managed_devices)
        self.state_service = StateService(state_history_size)
        self.threshold_service = ThresholdService(threshold_rules, enabled=True)
        self.ai_service = AIService(model_path=ai_model_path, enabled=ai_enabled)
        # Recent-command cache to avoid duplicate immediate sends when both
        # AI and Threshold trigger the same action nearly simultaneously.
        self._recent_commands: Dict[Tuple[str, str], float] = {}
        self._recent_command_ttl: float = 1.0  # seconds
        
        # Keep attributes for backward compatibility with existing integrations.
        self.managed_devices = self.device_service.managed_devices
        self.state_history_size = self.state_service.history_size
        self.latest_states = self.state_service.latest_states
        self.last_update_timestamp: Dict[str, float] = {}
        self.rate_limit_mqtt = rate_limit_mqtt
        self.rate_limit_serial = rate_limit_serial
        self.threshold_rules = self.threshold_service.get_rules()
        self.threshold_action_state = self.threshold_service.action_state
        self.use_ai = ai_enabled and self.ai_service.is_enabled()
        
        # Command queue for sequential threshold-triggered sends (thread-safe Queue)
        # self.command_queue = Queue()
        # self.queue_processor_running = False
        # self.queue_processor_thread = None
        # # Timestamp of last serial send (monotonic). Used to minimize waits.
        # self._last_send_time = 0.0
        # self._start_queue_processor()
        # # Batch mode: send multiple queued commands back-to-back with small inter-command delay
        # # This reduces per-command latency while keeping a safe spacing between batches.
        # self.batch_mode = batch_mode
        # self.inter_command_delay = inter_command_delay  # seconds between commands in a batch
        
        self.mqtt.set_callback(self._on_mqtt)
        self.serial.set_callback(self._on_serial)
        
        logger.info(f"Router initialized | limits: mqtt={rate_limit_mqtt}s serial={rate_limit_serial}s")

    def _append_state_from_kit(self, device_name: str, value: Any) -> None:
        """Append state to bounded history when status is received from kit."""
        self.state_service.append_from_kit(
            device_name=device_name,
            value=value,
            is_sensor=self._is_sensor_device(device_name),
        )

    def _normalize_threshold_value(self, target_device: str, value: Any) -> str:
        """Normalize threshold command value for the target device."""
        normalized = str(value).strip()
        if self._is_switch_device(target_device):
            if normalized in {"on", "off"}:
                return self._action_to_value(normalized)
        return normalized

    def _check_threshold(self, device_name: str, value: Any) -> None:
        """Check internal automation (threshold or AI) and act on target device.
        
        Dispatches to either AI-based or threshold-based automation depending on
        use_ai flag and available sensor data.
        
        Queues commands for sequential serial sends (throttled by mqtt_to_serial interval).
        """
        if not self._is_sensor_device(device_name):
            return

        def send_command(target_device, desired_value):
            # Add to command queue instead of sending directly
            # Queue processor will throttle sends with mqtt_to_serial interval
            self._enqueue_command(target_device, desired_value)

        # Try AI-based automation first if enabled
        if self.use_ai:
            sensor_dict = self._get_sensor_dict()
            if sensor_dict:
                # Run AI triggers but do not short-circuit; allow threshold
                # rules to run as well so both systems can propose actions.
                self.ai_service.check_and_trigger(sensor_dict, send_command)
        
        # Fall back to threshold-based automation
        self.threshold_service.check_threshold(device_name, value, send_command)

    def _enqueue_command(self, device_name: str, value: Any) -> None:
        """Add command to queue for sequential sending (non-blocking, like MQTT publish).
        
        Args:
            device_name: Device to control.
            value: Command value.
        """
        # Queue processing has been disabled — send immediately to serial.
        # This simplifies behavior and avoids AttributeError when queue
        # is not initialized in simpler deployments.
        # Queue processing disabled — send immediately but avoid duplicates
        # when AI and threshold both fire the same command within short time.
        key = (str(device_name), str(value))
        now = time.monotonic()
        last = self._recent_commands.get(key, 0.0)
        if now - last < getattr(self, '_recent_command_ttl', 1.0):
            logger.debug(f"Deduped immediate send: {device_name}={value}")
            return
        self._recent_commands[key] = now
        logger.debug(f"Immediate send: {device_name}={value}")
        try:
            self._to_serial(device_name, value)
        except Exception as e:
            logger.exception(f"Immediate send failed: {e}")
    
    def _start_queue_processor(self) -> None:
        """Start background daemon thread to process command queue continuously."""
        # Queue processor disabled in this build; no background thread started.
        logger.debug("_start_queue_processor(): queue processing disabled")
    
    def _process_command_queue(self) -> None:
        """Background daemon thread that continuously processes queued commands with rate limiting.
        
        Blocks on Queue.get() with timeout, so minimal CPU usage while waiting for commands.
        """
        # Queue processing removed — this method is retained as a no-op
        # for compatibility with cleanup()/tests that may call it.
        logger.debug("_process_command_queue(): disabled")
        return
    
    def _stop_queue_processor(self) -> None:
        """Stop background queue processor thread gracefully."""
        # No queue processor to stop when disabled.
        logger.debug("_stop_queue_processor(): queue processing disabled")

    def _get_sensor_dict(self) -> Optional[Dict[str, float]]:
        """Get current sensor values for AI model input.
        
        Returns:
            Dict with keys 'light', 'temp', 'humi' mapped to latest values,
            or None if any required sensor missing.
        """
        sensor_mapping = {
            'light': 'light',
            'temp': 'temp',
            'humi': 'humi'
        }
        
        sensor_dict = {}
        for key, sensor_name in sensor_mapping.items():
            value = self.state_service.state(sensor_name)
            if value is None:
                logger.debug(f"Missing sensor data for AI: {sensor_name}")
                return None
            try:
                sensor_dict[key] = float(value)
            except (ValueError, TypeError):
                logger.debug(f"Invalid sensor value: {sensor_name}={value}")
                return None
        
        return sensor_dict


    def get_sensor_state_history(self, device: str) -> list:
        """Get recent states for one sensor device."""
        return self.state_service.get_sensor_history(device)

    def get_device_state_history(self, device: str) -> list:
        """Get recent states for one controllable device."""
        return self.state_service.get_device_history(device)

    def _is_sensor_device(self, device: str) -> bool:
        """Check whether a mapped property should be published as sensor topic."""
        return self.device_service.is_sensor(device)

    def _is_actuator_device(self, device: str) -> bool:
        """Check whether a mapped property should be treated as controllable device."""
        return self.device_service.is_managed(device) and not self.device_service.is_sensor(device)
    
    def _is_switch_device(self, device: str) -> bool:
        """Check if device is a switch (led, fan).
        
        Args:
            device: Device identifier.
            
        Returns:
            True if device is switch type.
        """
        return self.device_service.is_switch(device)
    
    def _action_to_value(self, action: str) -> str:
        """Convert on/off action to serial value.
        
        Args:
            action: 'on' or 'off'.
            
        Returns:
            '1' for on, '0' for off.
        """
        return self.device_service.action_to_value(action)
    
    def _value_to_action(self, value: str) -> str:
        """Convert serial value to on/off action.
        
        Args:
            value: '1' or '0' (or any string).
            
        Returns:
            'on' for '1', 'off' for '0'.
        """
        return self.device_service.value_to_action(value)

    
    def _ok_to_send(self, key: str, interval: float) -> bool:
        """Check if message rate limit has elapsed for this key.
        
        Args:
            key: Unique identifier for rate limit tracking.
            interval: Minimum seconds required between messages.
            
        Returns:
            True if enough time has passed, False if rate limited.
            
        Side Effects:
            Updates last_update_timestamp[key] when returning True.
        """
        now = datetime.now().timestamp()
        last = self.last_update_timestamp.get(key, 0)
        
        if now - last < interval:
            return False
        
        self.last_update_timestamp[key] = now
        return True
    
    def _on_mqtt(self, topic: str, payload: str):
        """Process incoming MQTT message.
        
        Routes to command handlers (getall, device get) or forwards to device
        via serial. Rate limits MQTT→Serial messages.
        
        Args:
            topic: MQTT topic string.
            payload: JSON string with either 'value' or 'action' field.
            
        Logs:
            Errors for invalid JSON, rate limiting, and exceptions.
        """
        try:
            logger.debug(f"← MQTT {topic}: {payload}")

            if topic == self.topic_system_getall:
                self._getall()
                return
            
            parsed_topic = self.adapter.parse_topic(topic)
            if not parsed_topic:
                logger.debug(f"Ignored topic (schema mismatch): {topic}")
                return

            if parsed_topic.get('kind') == 'system' and parsed_topic.get('action') == 'getall':
                self._getall()
                return

            if parsed_topic.get('kind') != 'entity':
                return

            if parsed_topic.get('device_type') != 'device':
                logger.debug(f"Ignoring non-device command topic: {topic}")
                return

            if parsed_topic.get('action_or_status') != 'set':
                logger.debug(f"Ignoring non-set device topic: {topic}")
                return

            device_name = parsed_topic.get('property', '')
            if not device_name:
                return

            if not self.device_service.is_managed(device_name):
                logger.warning(f"Ignoring unmanaged device command: {device_name}")
                return
            
            try:
                data = self.adapter.from_mqtt(payload)
            except ValueError as e:
                logger.error(f"Invalid MQTT payload: {e}")
                return
            
            action = data.get("action")
            if action is None:
                logger.warning(f"Device payload must include action for {device_name}: {payload}")
                return

            if self._is_switch_device(device_name):
                value = self._action_to_value(action)
            else:
                # Non-switch device uses action as command value (e.g. servo action "90").
                value = str(action)
            
            if not self._ok_to_send(f"mqtt_{device_name}", self.rate_limit_mqtt):
                logger.debug(f"Rate limited: mqtt_{device_name}")
                return
            
            # Do not update state list here. State is authoritative only when
            # periodic status comes back from kit over serial.
            self._to_serial(device_name, value)
            
        except Exception as e:
            logger.error(f"MQTT callback error: {e}")
    
    def _on_serial(self, raw_data: str):
        """Process incoming serial message from device.
        
        Parses serial format and forwards to MQTT. Rate limits Serial→MQTT
        messages.
        
        Args:
            raw_data: Serial frame in format '!{abbr}:{value}#'.
            
        Logs:
            Errors for parse failures and exceptions.
        """
        logger.debug(f"← Serial {raw_data}")
        
        try:
            frames = self._split_serial_frames(raw_data)
            if not frames:
                logger.warning(f"Invalid serial: {raw_data}")
                return

            for frame in frames:
                result = self.adapter.from_serial(frame)
                if not result:
                    logger.warning(f"Invalid serial frame: {frame}")
                    continue

                device_name, value = result

                if not self._ok_to_send(f"serial_{device_name}", self.rate_limit_serial):
                    logger.debug(f"Rate limited: serial_{device_name}")
                    continue

                # Update histories only with data returned from kit.
                self._append_state_from_kit(device_name, value)

                # Run internal threshold automation rules before publishing state.
                self._check_threshold(device_name, value)

                # Publish kit state to MQTT.
                self._to_mqtt(device_name, value)
            
        except Exception as e:
            logger.error(f"Serial parse error: {e}")

    def _split_serial_frames(self, raw_data: str) -> List[str]:
        """Split raw serial data into one or more frames '!...#'."""
        if not raw_data:
            return []

        # Supports both spaced and concatenated batches, e.g. '!T:27#!H:50#'.
        frames = re.findall(r"![^!#]+#", raw_data)
        if frames:
            return frames

        cleaned = raw_data.strip()
        if cleaned.startswith("!") and cleaned.endswith("#"):
            return [cleaned]
        return []
    
    def _to_serial(self, device_name: str, value: Any) -> bool:
        """Send control command to serial device.
        
        Args:
            device_name: Device identifier (e.g., 'led', 'fan').
            value: Command value.
            
        Returns:
            True if send succeeded, False on error.
            
        Raises:
            Catches all exceptions and logs.
        """
        try:
            frame = self.adapter.to_serial({'device': device_name, 'value': value})
            if hasattr(self.serial, 'send_packet'):
                ok = self.serial.send_packet(frame)
            else:
                ok = self.serial.send(frame)
            
            if ok:
                logger.info(f"→ Serial {frame}")
            else:
                logger.warning(f"Serial send failed: {frame}")
            
            return ok
        except Exception as e:
            logger.error(f"Serial send error: {e}")
            return False
    
    def _to_mqtt(self, device_name: str, value: Any) -> bool:
        """Publish device state update to MQTT.
        
        Args:
            device_name: Device identifier.
            value: Current state value.
            
        Returns:
            True if publish succeeded, False on error.
        """
        try:
            if self._is_sensor_device(device_name):
                topic = self.adapter.build_topic(
                    property_name=device_name,
                    device_type='sensor',
                )
                payload = json.dumps({"value": str(value)})
            else:
                topic = self.adapter.build_topic(
                    property_name=device_name,
                    device_type='device',
                    action_or_status='state',
                )
                if self._is_switch_device(device_name):
                    payload = json.dumps({"action": self._value_to_action(value)})
                else:
                    payload = json.dumps({"action": str(value)})
            
            self.mqtt.publish(topic, payload)
            logger.info(f"→ MQTT {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False
    
    def state(self, device: str) -> Optional[Any]:
        """Get current device state.
        
        Args:
            device: Device identifier.
            
        Returns:
            Current value or None if not seen.
        """
        return self.latest_states.get(str(device).lower())
    
    def states(self) -> Dict[str, Any]:
        """Get all device states.
        
        Returns:
            Copy of device_states dict.
        """
        return self.state_service.states()
    
    def _getall(self):
        """Publish full state snapshot to system stateall topic.
        
        Returns complete state for ALL devices in mapping.
        Devices without values are set to null.
        
        Example output:
            {
              "temp": "25.5",
              "humi": null,
              "light": null,
              "led": "1",
              "fan": null,
              "servo": null
            }
        
        Raises:
            Catches all exceptions and logs.
        """
        try:
            # Include ALL managed devices from config.
            all_devices = self.managed_devices
            states = {}
            
            for device_name in all_devices.keys():
                value = self.state_service.state(device_name)
                # Convert to string if value exists, otherwise None (becomes "null" in JSON)
                states[device_name] = str(value) if value is not None else None
            
            payload = json.dumps(states)
            self.mqtt.publish(self.topic_system_state_all, payload)
            logger.info(f"→ MQTT {self.topic_system_state_all}: {payload}")
            
        except Exception as e:
            logger.error(f"Getall error: {e}")
    
    def _get_device(self, device: str):
        """Publish single device state to state/{device} topic.
        
        Args:
            device: Device identifier.
            
        Raises:
            Catches all exceptions and logs.
        """
        try:
            device_key = str(device).lower()
            if not self.device_service.is_managed(device_key):
                logger.warning(f"Get device ignored: unmanaged device '{device_key}'")
                return

            state = self.state_service.state(device_key)
            if state is None:
                state = "unknown"
            if self._is_sensor_device(device_key):
                topic = self.adapter.build_topic(
                    property_name=device_key,
                    device_type='sensor',
                )
                payload = json.dumps({"value": str(state)})
            else:
                topic = self.adapter.build_topic(
                    property_name=device_key,
                    device_type='device',
                    action_or_status='state',
                )
                if self._is_switch_device(device_key):
                    payload = json.dumps({"action": self._value_to_action(state)})
                else:
                    payload = json.dumps({"action": str(state)})
            
            self.mqtt.publish(topic, payload)
            logger.info(f"→ MQTT {topic}: {payload}")
        except Exception as e:
            logger.error(f"Get device error: {e}")
    
    def cmd(self, device: str, value: Any) -> bool:
        """Send manual command to device via serial.
        
        Args:
            device: Device identifier.
            value: Command value.
            
        Returns:
            True if send succeeded.
        """
        device_key = str(device).lower()
        if not self.device_service.is_managed(device_key):
            logger.warning(f"Manual command ignored: unmanaged device '{device_key}'")
            return False
        logger.info(f"Manual: {device_key}={value}")
        return self._to_serial(device_key, value)
    
    def emit(self, device: str, value: Any) -> bool:
        """Publish manual state update to MQTT.
        
        Args:
            device: Device identifier.
            value: State value.
            
        Returns:
            True if publish succeeded.
        """
        device_key = str(device).lower()
        if not self.device_service.is_managed(device_key):
            logger.warning(f"Emit ignored: unmanaged device '{device_key}'")
            return False
        logger.info(f"Emit: {device_key}={value}")
        return self._to_mqtt(device_key, value)

    def set_threshold_enabled(self, enabled: bool) -> None:
        """Enable or disable threshold automation."""
        self.threshold_service.set_enabled(enabled)

    def is_threshold_enabled(self) -> bool:
        """Check if threshold automation is enabled."""
        return self.threshold_service.is_enabled()

    def get_threshold_status(self) -> Dict[str, Any]:
        """Get threshold service status."""
        return self.threshold_service.get_status()

    def update_threshold_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Update threshold rules.
        
        Args:
            rules: List of threshold rule dicts.
        """
        self.threshold_service.update_rules(rules)
        self.threshold_rules = self.threshold_service.get_rules()

    def set_ai_enabled(self, enabled: bool) -> None:
        """Enable or disable AI-based automation.
        
        Args:
            enabled: Whether to use AI instead of threshold rules.
        """
        if not self.ai_service.is_enabled() and enabled:
            logger.warning("AI service not available (model not loaded)")
            return
        self.ai_service.set_enabled(enabled)
        self.use_ai = enabled
        logger.info(f"AI automation {'enabled' if enabled else 'disabled'}")

    def is_ai_enabled(self) -> bool:
        """Check if AI-based automation is enabled and active."""
        return self.use_ai and self.ai_service.is_enabled()

    def get_ai_status(self) -> Dict[str, Any]:
        """Get AI service status including model info."""
        status = self.ai_service.get_status()
        status['model_info'] = self.ai_service.get_model_info()
        return status

    def get_automation_status(self) -> Dict[str, Any]:
        """Get combined status of both threshold and AI automation."""
        active_mode = 'None'
        if self.is_ai_enabled():
            active_mode = 'AI'
        elif self.is_threshold_enabled():
            active_mode = 'Threshold'

        return {
            'threshold': self.get_threshold_status(),
            'ai': self.get_ai_status(),
            'active_mode': active_mode
        }


    def device_info(self, device: str) -> Optional[Dict[str, Any]]:
        """Return full metadata and state/history for a managed device.

        Returns None when device is not managed.
        """
        key = str(device).lower()
        is_sensor = self.device_service.is_sensor(key)
        history = self.state_service.get_sensor_history(key) if is_sensor else self.state_service.get_device_history(key)
        return self.device_service.device_info(
            device=key,
            latest_state=self.state_service.state(key),
            history=history,
            history_size_limit=self.state_history_size,
        )

    def all_devices_info(self) -> Dict[str, Dict[str, Any]]:
        """Return complete information for all managed devices.

        Note:
            `serial_abbr` is intentionally omitted from this aggregated API.
        """
        result: Dict[str, Dict[str, Any]] = {}
        for name in self.managed_device_list():
            info = self.device_info(name)
            if not info:
                continue

            info_without_abbr = dict(info)
            info_without_abbr.pop('serial_abbr', None)
            result[name] = info_without_abbr

        return result
    
    def cleanup(self) -> None:
        """Clean up resources: stop command queue processor."""
        self._stop_queue_processor()