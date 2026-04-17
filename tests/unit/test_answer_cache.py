from __future__ import annotations

from src.api.v1.answer_cache import AnswerCache


def test_key_normalizes_case_and_whitespace() -> None:
    k1 = AnswerCache._key('nalla', 'Is chocolate safe?')
    k2 = AnswerCache._key('nalla', '  is CHOCOLATE safe?  ')
    assert k1 == k2


def test_key_differs_per_chatflow() -> None:
    assert AnswerCache._key('nalla', 'hi') != AnswerCache._key('other', 'hi')


def test_key_differs_per_question() -> None:
    assert AnswerCache._key('nalla', 'is chocolate safe?') != AnswerCache._key(
        'nalla', 'are grapes safe?'
    )


def test_key_format() -> None:
    key = AnswerCache._key('nalla', 'is chocolate safe?')
    assert key.startswith('answer_cache:nalla:')
    assert len(key.split(':')[-1]) == 32  # sha256[:32]
