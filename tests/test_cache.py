import pytest

from jevmock import JevApiError, jevmock
from jevmock.cache import TtlCache
from jevmock.errors import JevSignatureError
from tests.fake_transport import FakeTransport


def test_same_arguments_are_answered_from_cache():
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(ttl=60, transport=transport)
    def is_odd(x: int) -> bool: ...

    assert is_odd(3) is True
    assert is_odd(3) is True
    assert len(transport.requests) == 1


def test_positional_and_keyword_and_default_share_one_key():
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(ttl=60, transport=transport)
    def is_odd(x: int, base: int = 10) -> bool: ...

    assert is_odd(3) is True
    assert is_odd(x=3) is True
    assert is_odd(3, 10) is True
    assert len(transport.requests) == 1


def test_different_arguments_are_asked_again():
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(ttl=60, transport=transport)
    def is_odd(x: int) -> bool: ...

    assert is_odd(3) is True
    assert is_odd(4) is False
    assert len(transport.requests) == 2


def test_expired_entry_is_asked_again(monkeypatch):
    now = 1000.0
    monkeypatch.setattr("jevmock.cache.monotonic", lambda: now)
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(ttl=30, transport=transport)
    def is_odd(x: int) -> bool: ...

    assert is_odd(3) is True
    now = 1031.0
    assert is_odd(3) is False
    assert len(transport.requests) == 2


def test_without_ttl_every_call_is_sent():
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(transport=transport)
    def is_odd(x: int) -> bool: ...

    assert is_odd(3) is True
    assert is_odd(3) is False
    assert len(transport.requests) == 2


def test_failed_answer_is_not_cached():
    transport = FakeTransport([{"noul": "0.9"}, {"noul": 0.97}])

    @jevmock(ttl=60, transport=transport)
    def is_odd(x: int) -> bool: ...

    with pytest.raises(JevApiError):
        is_odd(3)
    assert is_odd(3) is True
    assert len(transport.requests) == 2


def test_two_functions_do_not_share_cache():
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(ttl=60, transport=transport)
    def is_odd(x: int) -> bool: ...

    @jevmock(ttl=60, transport=transport)
    def is_even(x: int) -> bool: ...

    assert is_odd(3) is True
    assert is_even(3) is False
    assert len(transport.requests) == 2


def test_non_positive_ttl_is_signature_error():
    with pytest.raises(JevSignatureError):

        @jevmock(ttl=0)
        def is_odd(x: int) -> bool: ...


def test_set_discards_expired_entries(monkeypatch):
    now = 1000.0
    monkeypatch.setattr("jevmock.cache.monotonic", lambda: now)
    cache = TtlCache(30)

    cache.set("a", 1)
    now = 1031.0
    cache.set("b", 2)
    assert list(cache._entries) == ["b"]
