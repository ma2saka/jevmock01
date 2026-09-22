from enum import Enum
from typing import Literal

import pytest

from jevmock.errors import JevSignatureError
from jevmock.json_value import JsonObject
from jevmock.questions import ANSWER_KEY, ChoiceQuestion, NoulQuestion, ScoreQuestion
from jevmock.signature import MockSpec, build_spec


def answer_of(spec: MockSpec[str] | MockSpec[float], raw: JsonObject) -> object:
    """1件の答えを含む応答を組み立て、spec に復号させる。"""
    return spec.answer({"answers": {ANSWER_KEY: raw}})


class Verdict(Enum):
    ALLOW = "問題なく許可できる"
    DENY = "拒否すべき"


def is_odd(x: int) -> bool: ...
def verdict_of(text: str) -> Verdict: ...
def label_of(text: str) -> Literal["red", "green"]: ...
def team_for(text: str) -> str: ...
def anger_of(text: str) -> int: ...
def ratio_of(text: str) -> float: ...
def untyped(x): ...
def unsupported(x: int) -> list[str]: ...


def test_bool_becomes_noul():
    spec = build_spec(is_odd)
    assert isinstance(spec.question, NoulQuestion)
    assert answer_of(spec, {"noul": 0.9}) is True
    assert answer_of(spec, {"noul": 0.4}) is False


def test_enum_becomes_choice_over_member_names():
    spec = build_spec(verdict_of)
    assert isinstance(spec.question, ChoiceQuestion)
    assert spec.question.criteria == {"ALLOW": Verdict.ALLOW.value, "DENY": Verdict.DENY.value}
    assert answer_of(spec, {"choice": "DENY"}) is Verdict.DENY


def test_literal_becomes_choice():
    spec = build_spec(label_of)
    assert isinstance(spec.question, ChoiceQuestion)
    assert list(spec.question.criteria) == ["red", "green"]
    assert answer_of(spec, {"choice": "green"}) == "green"


def test_str_needs_choice():
    spec = build_spec(team_for, choice=["billing", "technical"])
    assert isinstance(spec.question, ChoiceQuestion)
    assert answer_of(spec, {"choice": "billing"}) == "billing"
    with pytest.raises(JevSignatureError):
        build_spec(team_for)


def test_score_levels_and_rounding():
    levels = ["穏やか", "苛立ち", "激怒"]
    assert answer_of(build_spec(anger_of, score=levels), {"score": 1.4}) == 1
    assert answer_of(build_spec(ratio_of, score=levels), {"score": 1.4}) == 1.4
    assert isinstance(build_spec(anger_of, score=levels).question, ScoreQuestion)


def test_float_without_score_is_noul_probability():
    spec = build_spec(ratio_of)
    assert isinstance(spec.question, NoulQuestion)
    assert answer_of(spec, {"noul": 0.25}) == 0.25


def test_rejections():
    with pytest.raises(JevSignatureError):
        build_spec(untyped)
    with pytest.raises(JevSignatureError):
        build_spec(unsupported)
    with pytest.raises(JevSignatureError):
        build_spec(anger_of)
    with pytest.raises(JevSignatureError):
        build_spec(verdict_of, choice=["ALLOW"])
    with pytest.raises(JevSignatureError):
        build_spec(team_for, choice=["a"], score=["x", "y"])


def test_state_binds_arguments_with_defaults():
    def compare(left: int, right: int = 3) -> bool: ...

    spec = build_spec(compare)
    assert spec.state((1,), {}) == {"arguments": {"left": 1, "right": 3}}
    assert "compare" in spec.instructions
