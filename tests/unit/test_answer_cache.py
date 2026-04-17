from __future__ import annotations

from src.api.v1.answer_cache import AnswerCache


def test_key_normalizes_case_and_whitespace() -> None:
    k1 = AnswerCache._key('', 'nalla', 'Is chocolate safe?')
    k2 = AnswerCache._key('', 'nalla', '  is CHOCOLATE safe?  ')
    assert k1 == k2


def test_key_differs_per_chatflow() -> None:
    assert AnswerCache._key('', 'nalla', 'hi') != AnswerCache._key('', 'other', 'hi')


def test_key_differs_per_question() -> None:
    assert AnswerCache._key('', 'nalla', 'is chocolate safe?') != AnswerCache._key(
        '', 'nalla', 'are grapes safe?'
    )


def test_key_format_no_prefix() -> None:
    key = AnswerCache._key('', 'nalla', 'is chocolate safe?')
    assert key.startswith('answer_cache:nalla:')
    assert len(key.split(':')[-1]) == 32  # sha256[:32]


def test_key_with_prefix() -> None:
    key = AnswerCache._key('cookbot', 'nalla', 'hi')
    assert key.startswith('cookbot:answer_cache:nalla:')


def test_key_isolates_agents_with_same_chatflow() -> None:
    """Two agents using the same chatflow_id still get distinct keys."""
    k_nalla = AnswerCache._key('nalla', 'widget', 'hi')
    k_cookbot = AnswerCache._key('cookbot', 'widget', 'hi')
    assert k_nalla != k_cookbot
