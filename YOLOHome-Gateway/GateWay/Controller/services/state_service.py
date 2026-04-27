"""State cache and bounded history helpers for MainController."""

from collections import deque
from typing import Any, Dict, List


class StateService:
    """Keeps latest state and bounded history for sensor/device values."""

    def __init__(self, history_size: int):
        self.history_size = max(1, int(history_size))
        self.latest_states: Dict[str, Any] = {}
        self.device_state_history: Dict[str, deque] = {}
        self.sensor_state_history: Dict[str, deque] = {}

    def append_from_kit(self, device_name: str, value: Any, is_sensor: bool) -> None:
        key = str(device_name).lower()
        normalized_value = str(value)

        target = self.sensor_state_history if is_sensor else self.device_state_history
        if key not in target:
            target[key] = deque(maxlen=self.history_size)

        target[key].append(normalized_value)
        self.latest_states[key] = normalized_value

    def get_sensor_history(self, device: str) -> List[str]:
        return list(self.sensor_state_history.get(str(device).lower(), []))

    def get_device_history(self, device: str) -> List[str]:
        return list(self.device_state_history.get(str(device).lower(), []))

    def state(self, device: str):
        return self.latest_states.get(str(device).lower())

    def states(self) -> Dict[str, Any]:
        return self.latest_states.copy()
