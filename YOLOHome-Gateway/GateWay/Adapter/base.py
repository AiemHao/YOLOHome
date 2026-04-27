"""Abstract interface for format translators.

Adapters convert between MQTT (JSON), Serial (binary frames), and internal
state representations. Each adapter defines the protocol specifics.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class DataAdapter(ABC):
    """Base class for message format translators.
    
    Implementations must handle bidirectional translation between:
    - MQTT topics and device names
    - MQTT JSON payloads and internal dicts
    - Serial binary frames and internal dicts
    """
    
    @abstractmethod
    def build_topic(
        self,
        property_name: str,
        device_type: str,
        action_or_status: Optional[str] = None,
    ) -> str:
        """Build MQTT topic from structured parts.

        Args:
            property_name: Device/sensor name. Example: 'temp', 'led'.
            device_type: 'sensor' or 'device'.
            action_or_status: Optional suffix (e.g., 'set', 'state').

        Returns:
            Formatted MQTT topic following YOLOHome schema.
        """
        pass

    @abstractmethod
    def parse_topic(self, topic: str) -> Optional[Dict[str, str]]:
        """Parse MQTT topic into structured components.

        Returns:
            Dict with keys depending on topic type.
            - System topic: {'kind': 'system', 'action': 'getall'}
            - Device/Sensor topic:
                {
                    'kind': 'entity',
                    'location': 'livingroom',
                    'device_type': 'sensor'|'device',
                    'property': 'temp'|'led'|...
                    'action_or_status': 'set'|'state'|''
                }
            Returns None if topic is invalid.
        """
        pass

    @abstractmethod
    def to_serial(self, data: Dict[str, Any]) -> str:
        """Convert internal dict to serial frame.
        
        Args:
            data: Dict with 'device' and 'value' keys.
                Example: {'device': 'led', 'value': 1}
            
        Returns:
            Serial frame string. Example: '!L:1#'
            
        Raises:
            ValueError: If device unknown or value invalid.
        """
        pass
    
    @abstractmethod
    def from_serial(self, raw: str) -> Optional[Tuple[str, str]]:
        """Parse serial frame to internal dict.
        
        Args:
            raw: Serial frame string. Example: '!T:25.5#'
            
        Returns:
            Tuple (device_name, value) or None if invalid.
            Example: ('temp', '25.5')
        """
        pass
    
    @abstractmethod
    def to_mqtt_topic(self, device: str) -> str:
        """Convert device name to MQTT topic.
        
        Args:
            device: Device identifier. Example: 'led'
            
        Returns:
            MQTT topic.

        Note:
            Kept for backward compatibility. New code should prefer build_topic().
        """
        pass
    
    @abstractmethod
    def from_mqtt_topic(self, topic: str) -> str:
        """Extract device name from MQTT topic.
        
        Args:
            topic: MQTT topic. Example: 'home/led'
            
        Returns:
            Device identifier. Example: 'led'

        Note:
            Kept for backward compatibility. New code should prefer parse_topic().
        """
        pass
    
    @abstractmethod
    def from_mqtt(self, payload: str) -> Optional[Dict[str, Any]]:
        """Parse MQTT JSON payload.
        
        Args:
            payload: JSON string. Examples:
                - '{"value": "1"}'
                - '{"action": "get"}'
            
        Returns:
            Dict with 'value' and/or 'action' keys, or None if invalid.
            
        Raises:
            ValueError: If JSON invalid or missing required fields.
        """
        pass

