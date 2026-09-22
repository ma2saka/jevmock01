from enum import Enum

import pytest

from jevmock import JevApiError, jevmock
from jevmock.json_value import as_text
from tests.fake_transport import FakeTransport, asked


class Verdict(Enum):
    ALLOW = "問題なく許可できる"
    DENY = "拒否すべき"


def test_bool_function_returns_decoded_answer():
    transport = FakeTransport([{"noul": 0.97}, {"noul": 0.02}])

    @jevmock(transport=transport)
    def is_odd(x: int) -> bool: ...

    assert is_odd(3) is True
    assert is_odd(4) is False
    request = transport.requests[0]
    assert request["state"] == {"arguments": {"x": 3}}
    assert asked(transport)["type"] == "noul"
    assert request["model"] == "jev-latest"
    assert is_odd.__name__ == "is_odd"


def test_enum_function_returns_member():
    transport = FakeTransport([{"choice": "DENY"}])

    @jevmock(transport=transport)
    def verdict_of(text: str) -> Verdict:
        """発言を許可してよいか判定する。"""

    assert verdict_of("死ね") is Verdict.DENY
    question = asked(transport)
    assert question["criteria"] == {"ALLOW": Verdict.ALLOW.value, "DENY": Verdict.DENY.value}
    assert "発言を許可してよいか判定する。" in as_text(question["instructions"], "instructions")


def test_choice_outside_criteria_is_api_error():
    transport = FakeTransport([{"choice": "MAYBE"}])

    @jevmock(transport=transport)
    def verdict_of(text: str) -> Verdict: ...

    with pytest.raises(JevApiError):
        verdict_of("こんにちは")


def test_out_of_range_score_is_api_error():
    transport = FakeTransport([{"score": 9.0}])

    @jevmock(score=["穏やか", "苛立ち", "激怒"], transport=transport)
    def anger_of(text: str) -> int: ...

    with pytest.raises(JevApiError):
        anger_of("ふざけるな")


def test_malformed_answer_is_api_error():
    transport = FakeTransport([{"noul": "0.9"}])

    @jevmock(transport=transport)
    def is_odd(x: int) -> bool: ...

    with pytest.raises(JevApiError):
        is_odd(3)
