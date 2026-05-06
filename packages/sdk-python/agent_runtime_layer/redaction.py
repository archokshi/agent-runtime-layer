import re
from typing import Any


REDACTION_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)(api_key\s*=\s*)[^\s&]+"),
    re.compile(r"(?i)(password\s*=\s*)[^\s&]+"),
    re.compile(r"(?i)(token\s*=\s*)[^\s&]+"),
    re.compile(r"(?i)(secret\s*=\s*)[^\s&]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in REDACTION_PATTERNS:
        if pattern.pattern.startswith("(?i)("):
            redacted = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    if ".env" in redacted.lower() and ("=" in redacted or "preview" in redacted.lower()):
        return "[REDACTED_ENV_CONTENT]"
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value
