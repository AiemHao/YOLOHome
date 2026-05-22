"""Default adapter: MQTT/Serial translator with YOLOHome topic schema.

Protocol:
- Serial: !{ABBR}:{VALUE}# (e.g., !L:1#, !T:25.5#)
- MQTT topic:
    - Sensor: home/{room}/sensor/{type}
    - Command: home/{room}/device/{type}/set
    - Status: home/{room}/device/{type}/state
    - System: home/system/{action}
- MQTT payload:
    - Command set: JSON only, e.g. {"value": "1"} or {"action": "on"}
    - Status/Sensor: JSON only, e.g. {"value": "25.5"}

Devices: temp↔T, humi↔H, light↔Lu, led↔L, fan↔F, servo↔S
"""

from typing import Any, Dict, Optional, Tuple
import json
from .base import DataAdapter


class DefaultDataAdapter(DataAdapter):
    """Standard MQTT JSON ↔ Serial binary frame translator.
    
    Converts between MQTT topics/payloads and serial abbreviations/values.
    Device mapping configurable, defaults to standard home automation devices.
    """
    
    def __init__(
        self,
        device_mapping: Dict[str, str] = None,
        topic_prefix: str = "home",
        location: str = "livingroom",
    ):
        """Initialize adapter with device-to-abbreviation mapping.
        
        Args:
            device_mapping: Maps device names to serial abbreviations.
                If None, uses default: {'temp': 'T', 'led': 'L', ...}
        """
        if device_mapping is None:
            device_mapping = {
                "temp": "T",
                "humi": "H",
                "light": "Lu",
                "led": "L",
                "fan": "F",
                "servo": "S",
            }
        self.device_mapping = device_mapping
        self.topic_prefix = str(topic_prefix).strip("/") or "home"
        self.location = location.lower()

    def build_topic(
        self,
        property_name: str,
        device_type: str,
        action_or_status: Optional[str] = None,
    ) -> str:
        """Build topic using YOLOHome structured schema."""
        property_name = str(property_name).lower().strip()
        device_type = str(device_type).lower().strip()
        suffix = str(action_or_status or "").lower().strip()

        if device_type not in {"sensor", "device"}:
            raise ValueError(f"Unsupported device_type: {device_type}")
        if not property_name:
            raise ValueError("property_name is required")

        topic = f"{self.topic_prefix}/{self.location}/{device_type}/{property_name}"
        if suffix:
            topic = f"{topic}/{suffix}"
        return topic

    def parse_topic(self, topic: str) -> Optional[Dict[str, str]]:
        """Parse structured YOLOHome topic.

        Returns None if topic does not match expected schema.
        """
        if not topic:
            return None

        parts = [p.strip().lower() for p in topic.split("/") if p.strip()]
        if len(parts) == 3 and parts[0] == self.topic_prefix and parts[1] == "system":
            return {
                "kind": "system",
                "action": parts[2],
            }

        if len(parts) not in {4, 5}:
            return None

        prefix, location, device_type, property_name = parts[0], parts[1], parts[2], parts[3]
        suffix = parts[4] if len(parts) == 5 else ""

        if prefix != self.topic_prefix:
            return None
        if location != self.location:
            return None
        if device_type not in {"sensor", "device"}:
            return None

        return {
            "kind": "entity",
            "location": location,
            "device_type": device_type,
            "property": property_name,
            "action_or_status": suffix,
        }
    
    def to_serial(self, data: Dict[str, Any]) -> str:
        """Convert device dict to serial frame.
        
        Args:
            data: Dict with 'device' and 'value' keys.
                Examples: {'device': 'led', 'value': 1}
            
        Returns:
            Serial frame: '!L:1#'
            
        Raises:
            ValueError: If device unknown or missing.
        """
        device = str(data.get('device', '')).lower()
        value = str(data.get('value', ''))
        
        if not device or not value:
            raise ValueError(f"Missing device/value in {data}")
        
        abbr = self.device_mapping.get(device)
        if not abbr:
            raise ValueError(f"Unknown device: {device}")
        
        return f"!{abbr}:{value}#"

    def to_serial_batch(self, items: list) -> str:
        """Convert a list of device dicts to a single combined serial frame.

        Args:
            items: List of dicts like {'device': 'fan', 'value': '1'}

        Returns:
            Combined serial frame, e.g. '!F:1;L:1;S:1#'

        Notes:
            Separator between commands is ';'. Firmware must accept this format.
        """
        if not items:
            raise ValueError("items must be non-empty list")

        parts = []
        for it in items:
            dev = str(it.get('device', '')).lower()
            val = str(it.get('value', ''))
            if not dev or val == '':
                raise ValueError(f"Invalid item in batch: {it}")
            abbr = self.device_mapping.get(dev)
            if not abbr:
                raise ValueError(f"Unknown device in batch: {dev}")
            parts.append(f"{abbr}:{val}")

        body = ";".join(parts)
        return f"!{body}#"
    
    def from_serial(self, raw: str) -> Optional[Tuple[str, str]]:
        """Parse serial frame to (device, value) tuple.
        
        Args:
            raw: Serial frame string, e.g., '!T:25.5#'
            
        Returns:
            Tuple (device_name, value) or None if invalid.
        """
        if not raw or not raw.startswith("!") or not raw.endswith("#"):
            return None
        
        try:
            content = raw[1:-1]
            parts = content.split(":")
            if len(parts) != 2:
                return None
            
            abbr, value = parts
            for dev_name, dev_abbr in self.device_mapping.items():
                if dev_abbr == abbr:
                    return dev_name, value
            
            return abbr.lower(), value
        except Exception:
            return None
    
    def to_mqtt_topic(self, device: str) -> str:
        """Convert device name to MQTT topic.
        
        Args:
            device: Device identifier (any case).
            
        Returns:
            Sensor topic by default.
        """
        return self.build_topic(property_name=str(device), device_type="sensor")
    
    def from_mqtt_topic(self, topic: str) -> str:
        """Extract device name from MQTT topic.
        
        Args:
            topic: MQTT topic.
            
        Returns:
            Device identifier (lowercase).
        """
        parsed = self.parse_topic(topic)
        if not parsed or parsed.get("kind") != "entity":
            return ""
        return parsed.get("property", "")
    
    def from_mqtt(self, payload_str: str) -> Optional[Dict[str, Any]]:
        """Parse MQTT JSON payload.
        
        Args:
            payload_str: JSON string, e.g., '{"value": "1"}'
            
        Returns:
            Dict with 'value' or 'action' keys, or None if invalid.
            
        Raises:
            ValueError: If invalid JSON.
        """
        payload_str = "" if payload_str is None else str(payload_str).strip()
        if not payload_str:
            raise ValueError("Empty payload")

        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON payload: {payload_str}") from e

        if not isinstance(data, dict):
            raise ValueError(f"MQTT payload must be JSON object: {payload_str}")

        result = {}
        if 'action' in data:
            result['action'] = str(data['action']).lower()
        if 'value' in data:
            result['value'] = data['value']

        if not result:
            raise ValueError(f"Missing 'action' or 'value': {payload_str}")

        return result
    
    def to_mqtt(self, data: Dict[str, Any]) -> Optional[str]:
        """Serialize data to MQTT JSON payload.
        
        Args:
            data: Dict with 'value' or 'action' key.
            
        Returns:
            JSON string, e.g., '{"value": "1"}' or None if empty.
        """
        if not data:
            return None
        return json.dumps(data)
    
    def supports_device(self, device: str) -> bool:
        """Check if device is supported in mapping.
        
        Args:
            device: Device name (any case).
            
        Returns:
            True if device exists in mapping.
        """
        return str(device).lower() in self.device_mapping
    
    def set_device_mapping(self, mapping: Dict[str, str]) -> None:
        """Update device-to-abbreviation mapping.
        
        Args:
            mapping: Dict mapping devices to serial abbreviations.
        """
        self.device_mapping.update(mapping)
    
    def get_device_mapping(self) -> Dict[str, str]:
        """Get current device mapping.
        
        Returns:
            Copy of device-to-abbreviation mapping.
        """
        return self.device_mapping.copy()
