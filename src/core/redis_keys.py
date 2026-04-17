"""Helpers for building namespaced Redis keys.

All modules that write to Redis should build keys via :func:`prefixed_key` so
that multiple agents sharing one Redis instance cannot collide. The prefix
comes from ``Settings.redis_key_prefix`` — when empty, keys are returned
unchanged for backward compatibility with single-agent deployments.
"""

from __future__ import annotations


def prefixed_key(prefix: str, *parts: str) -> str:
    """Return ``{prefix}:{part1}:{part2}...`` (or ``{part1}:{part2}...`` if prefix is empty)."""
    body = ':'.join(parts)
    return f'{prefix}:{body}' if prefix else body
