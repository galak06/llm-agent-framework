import re

from src.core.config import Settings

_NULL_BYTES = re.compile(r'\x00')
_HTML_TAGS = re.compile(r'<[^>]+>')
_UNICODE_CTRL = re.compile(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]')


def sanitize_input(text: str, settings: Settings) -> str:
    """Strip dangerous characters and truncate to max length."""
    text = _NULL_BYTES.sub('', text)
    text = _HTML_TAGS.sub('', text)
    text = _UNICODE_CTRL.sub('', text)
    return text[: settings.allowed_input_max_length].strip()
