from typing import Callable
from typing import Any

from src.utils.logging.constants import REDACTED_PLACEHOLDER


class StructlogRedactionProcessor:
    def __init__(self, is_sensitive_key: Callable[[str], bool]):
        self._is_sensitive_key = is_sensitive_key

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: dict,
    ) -> dict:
        return self._redact_dict(event_dict)

    def _redact_dict(self, data: dict) -> dict:
        result = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                result[key] = REDACTED_PLACEHOLDER
            else:
                result[key] = self._redact_value(value)
        return result

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return self._redact_dict(value)
        if isinstance(value, (list, tuple)):
            redacted_items = []
            for item in value:
                redacted_items.append(self._redact_value(item))
            return type(value)(redacted_items)
        return value
