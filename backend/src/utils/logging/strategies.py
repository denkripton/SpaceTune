from src.utils.logging.constants import DEFAULT_REDACTION_MARKERS


def _normalize(value: str) -> str:
    return value.lower().replace("-", "").replace("_", "")


def is_sensitive_key(
    key: str,
    markers = DEFAULT_REDACTION_MARKERS,
) -> bool:
    normalized_key = _normalize(key)
    for marker in markers:
        if _normalize(marker) in normalized_key:
            return True
    return False