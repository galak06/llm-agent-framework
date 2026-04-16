from __future__ import annotations

from src.core.config import Settings
from src.core.security import sanitize_input


class TestSanitizeInput:
    def _settings(self, max_length: int = 500) -> Settings:
        return Settings(
            widget_api_key='k',
            admin_api_key='k',
            anthropic_api_key='k',
            database_url='postgresql+asyncpg://x',
            allowed_input_max_length=max_length,
        )

    def test_strips_null_bytes(self) -> None:
        result = sanitize_input('hello\x00world', self._settings())
        assert '\x00' not in result
        assert result == 'helloworld'

    def test_strips_html_tags(self) -> None:
        result = sanitize_input('<script>alert("xss")</script>hello', self._settings())
        assert '<script>' not in result
        assert 'hello' in result

    def test_strips_unicode_control_chars(self) -> None:
        result = sanitize_input('hello\x01\x02\x03world', self._settings())
        assert result == 'helloworld'

    def test_truncates_to_max_length(self) -> None:
        long_input = 'a' * 1000
        result = sanitize_input(long_input, self._settings(max_length=50))
        assert len(result) == 50

    def test_strips_whitespace(self) -> None:
        result = sanitize_input('  hello  ', self._settings())
        assert result == 'hello'

    def test_clean_input_unchanged(self) -> None:
        result = sanitize_input('Can my dog eat rice?', self._settings())
        assert result == 'Can my dog eat rice?'
