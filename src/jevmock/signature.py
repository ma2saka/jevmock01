"""関数のシグネチャから System One の質問と復号手順を組み立てる。"""

import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Literal, get_args, get_origin, get_type_hints

from .errors import JevSignatureError
from .json_value import JsonObject, JsonValue
from .questions import ChoiceQuestion, NoulQuestion, Question, ScoreQuestion, read_response

NOUL_THRESHOLD = 0.5

type Choices = Sequence[str] | Mapping[str, str | None]
type ChoiceSpec = tuple[ChoiceQuestion, Callable[[str], object]]
type NumberSpec = tuple[NoulQuestion | ScoreQuestion, Callable[[float], object]]


@dataclass(frozen=True)
class MockSpec[A]:
    """関数呼び出しを1回の System One 質問として表したもの。"""

    signature: inspect.Signature
    instructions: str
    question: Question[A]
    decode: Callable[[A], object]

    def state(self, args: tuple[object, ...], kwargs: Mapping[str, object]) -> JsonObject:
        """呼び出し引数を、質問に添える state に変換する。"""
        bound = self.signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return {"arguments": dict(bound.arguments)}

    def answer(self, response: JsonValue) -> object:
        """System One の応答を、関数の戻り値に復号する。"""
        return self.decode(read_response(response, self.question))


def _describe(func: Callable[..., object], signature: inspect.Signature) -> str:
    lines = [
        f"関数 {func.__name__}{signature} が返すべき値を判定する。",
        "state.arguments はその呼び出し引数。関数名と説明の意味に忠実に答える。",
    ]
    doc = inspect.getdoc(func)
    if doc:
        lines.insert(1, doc)
    return "\n".join(lines)


def _as_criteria(choices: Choices) -> Mapping[str, str | None]:
    if isinstance(choices, Mapping):
        return dict(choices)
    return {name: None for name in choices}


def _enum_question(instructions: str, enum: type[Enum]) -> ChoiceSpec:
    members = {member.name: str(member.value) for member in enum}
    if not members:
        raise JevSignatureError(f"{enum.__name__} に選択肢がありません")

    def decode(answer: str) -> object:
        return enum[answer]

    return ChoiceQuestion(instructions, members), decode


def _literal_question(instructions: str, values: Sequence[object]) -> ChoiceSpec:
    table = {str(value): value for value in values}
    if len(table) != len(values):
        raise JevSignatureError("Literal の選択肢が文字列として重複しています")

    def decode(answer: str) -> object:
        return table[answer]

    return ChoiceQuestion(instructions, dict.fromkeys(table, None)), decode


def _choice_question(instructions: str, choices: Choices) -> ChoiceSpec:
    criteria = _as_criteria(choices)
    if not criteria:
        raise JevSignatureError("choice が空です")

    def decode(answer: str) -> object:
        return answer

    return ChoiceQuestion(instructions, criteria), decode


def _score_question(instructions: str, levels: Sequence[str], as_int: bool) -> NumberSpec:
    if len(levels) < 2:
        raise JevSignatureError("score には2段階以上の評価基準が必要です")

    def decode(answer: float) -> object:
        if as_int:
            return round(answer)
        return answer

    return ScoreQuestion(instructions, list(levels)), decode


def _noul_question(instructions: str, as_bool: bool) -> NumberSpec:
    def decode(answer: float) -> object:
        if as_bool:
            return answer >= NOUL_THRESHOLD
        return answer

    return NoulQuestion(instructions), decode


def _return_type(func: Callable[..., object]) -> object:
    hints = get_type_hints(func)
    if "return" not in hints:
        raise JevSignatureError(f"{func.__name__} に戻り値の型注釈がありません")
    return hints["return"]


def build_spec(
    func: Callable[..., object],
    choice: Choices | None = None,
    score: Sequence[str] | None = None,
) -> MockSpec[str] | MockSpec[float]:
    """戻り値の型注釈と指定から、質問の種別と復号手順を決める。"""
    if choice is not None and score is not None:
        raise JevSignatureError("choice と score は同時に指定できません")
    signature = inspect.signature(func)
    instructions = _describe(func, signature)
    returns = _return_type(func)

    def choice_spec(built: ChoiceSpec) -> MockSpec[str]:
        return MockSpec(signature, instructions, *built)

    def number_spec(built: NumberSpec) -> MockSpec[float]:
        return MockSpec(signature, instructions, *built)

    if isinstance(returns, type) and issubclass(returns, Enum):
        if choice is not None:
            raise JevSignatureError("Enum を返す関数に choice は指定できません")
        return choice_spec(_enum_question(instructions, returns))

    if get_origin(returns) is Literal:
        if choice is not None:
            raise JevSignatureError("Literal を返す関数に choice は指定できません")
        return choice_spec(_literal_question(instructions, get_args(returns)))

    if returns is bool:
        if choice is not None or score is not None:
            raise JevSignatureError("bool を返す関数に choice と score は指定できません")
        return number_spec(_noul_question(instructions, as_bool=True))

    if returns is str:
        if choice is None:
            raise JevSignatureError("str を返す関数には choice の指定が必要です")
        return choice_spec(_choice_question(instructions, choice))

    if returns in (int, float):
        if score is not None:
            return number_spec(_score_question(instructions, score, as_int=returns is int))
        if returns is float:
            return number_spec(_noul_question(instructions, as_bool=False))
        raise JevSignatureError("int を返す関数には score の指定が必要です")

    raise JevSignatureError(f"戻り値の型に対応していません: {returns!r}")
