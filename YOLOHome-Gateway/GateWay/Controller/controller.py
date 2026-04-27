"""Main bus for MQTT ↔ Serial message routing.

Routes messages between MQTT broker and Serial device, applies rate limiting,
and maintains device state cache.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from .services import DeviceService, StateService

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
                 managed_devices: Dict[str, Dict[str, Any]] = None):
        """Initialize the message router.
        
        Args:
            mqtt_client: MQTT broker interface instance.
            serial_module: Serial device interface instance.
            data_adapter: Format translator (MQTT ↔ Serial ↔ JSON).
            rate_limit_mqtt: Minimum interval in seconds between MQTT→Serial messages.
            rate_limit_serial: Minimum interval in seconds between Serial→MQTT messages.
            mqtt_topics: Topic configuration dict with keys: getall, state_prefix, state_all.
        """
        self.mqtt = mqtt_client
        self.serial = serial_module
        self.adapter = data_adapter
        
        self.mqtt_topics = mqtt_topics or {}
        self.topic_system_getall = self.mqtt_topics.get('system_getall', 'home/system/getall')
        self.topic_system_state_all = self.mqtt_topics.get('system_state_all', 'home/system/stateall')
        self.device_service = DeviceService(self.adapter, managed_devices)
        self.state_service = StateService(state_history_size)
        # Keep attributes for backward compatibility with existing integrations.
        self.managed_devices = self.device_service.managed_devices
        self.state_history_size = self.state_service.history_size
        self.latest_states = self.state_service.latest_states
        self.last_update_timestamp: Dict[str, float] = {}
        self.rate_limit_mqtt = rate_limit_mqtt
        self.rate_limit_serial = rate_limit_serial
        
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

    def managed_device_list(self) -> List[str]:
        """Return all managed device names from configuration."""
        return self.device_service.managed_device_list()

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