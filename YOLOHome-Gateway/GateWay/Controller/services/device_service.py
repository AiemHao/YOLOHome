"""Device registry and action conversion utilities for MainController."""

from typing import Any, Dict, Optional, List


class DeviceService:
    """Encapsulates managed device metadata and related helper logic."""

    def __init__(self, adapter, managed_devices: Optional[Dict[str, Dict[str, Any]]] = None):
        self.adapter = adapter
        self.managed_devices = self._build_managed_devices(managed_devices)

    def _build_managed_devices(self, managed_devices: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        normalized: Dict[str, Dict[str, Any]] = {}
        raw = managed_devices or {}
        serial_mapping = self.adapter.get_device_mapping()

        for name, info in raw.items():
            key = str(name).lower().strip()
            metadata = info if isinstance(info, dict) else {}
            device_type = str(metadata.get("type", "")).lower().strip()
            if device_type not in {"sensor", "device"}:
                continue

            normalized[key] = {
                "type": device_type,
                "serial_abbr": str(serial_mapping.get(key, "")).strip(),
                "is_switch": bool(metadata.get("is_switch", False)),
                "unit": str(metadata.get("unit", "")).strip(),
                "description": str(metadata.get("description", "")).strip(),
            }

        if not normalized:
            for name, abbr in serial_mapping.items():
                key = str(name).lower().strip()
                inferred_type = "sensor" if key in {"temp", "humi", "light"} else "device"
                normalized[key] = {
                    "type": inferred_type,
                    "serial_abbr": str(abbr),
                    "is_switch": key in {"led", "fan", "servo"},
                    "unit": "",
                    "description": "",
                }

        return normalized

    def is_managed(self, device: str) -> bool:
        return str(device).lower() in self.managed_devices

    def is_sensor(self, device: str) -> bool:
        info = self.managed_devices.get(str(device).lower())
        return bool(info and info.get("type") == "sensor")

    def is_switch(self, device: str) -> bool:
        info = self.managed_devices.get(str(device).lower())
        return bool(info and info.get("is_switch"))

    def action_to_value(self, action: str) -> str:
        lowered = str(action).lower().strip()
        return "1" if lowered in {"on", "1", "true"} else "0"

    def value_to_action(self, value: str) -> str:
        return "on" if str(value).strip() == "1" else "off"

    def managed_device_list(self) -> List[str]:
        return sorted(self.managed_devices.keys())

    def device_info(
        self,
        device: str,
        latest_state: Any,
        history: List[str],
        history_size_limit: int,
    ) -> Optional[Dict[str, Any]]:
        key = str(device).lower()
        base = self.managed_devices.get(key)
        if not base:
            return None

        device_type = base.get("type")
        return {
            **base,
            "name": key,
            "latest_state": latest_state,
            "history": history,
            "history_size_limit": history_size_limit,
            "topic_set": self.adapter.build_topic(key, "device", "set") if device_type == "device" else None,
            "topic_state": self.adapter.build_topic(key, "device", "state") if device_type == "device" else self.adapter.build_topic(key, "sensor"),
        }
