from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.v1.routes.prediction import PredictionRequest


def test_chat_id_accepts_flowise_uuid() -> None:
    req = PredictionRequest(question='hi', chatId='a1b2c3d4-e5f6-4789-b0a1-c2d3e4f56789')
    assert req.chatId == 'a1b2c3d4-e5f6-4789-b0a1-c2d3e4f56789'


def test_chat_id_defaults_to_none() -> None:
    req = PredictionRequest(question='hi')
    assert req.chatId is None


@pytest.mark.parametrize(
    'bad',
    [
        'has spaces',
        'slash/char',
        'colon:char',
        'quote"char',
        '',
        'a' * 129,
    ],
)
def test_chat_id_rejects_unsafe_values(bad: str) -> None:
    with pytest.raises(ValidationError):
        PredictionRequest(question='hi', chatId=bad)
