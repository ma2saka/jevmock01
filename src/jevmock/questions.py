"""System One の質問プリミティブと、その応答の読み取り。"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from .errors import JevApiError
from .json_value import JsonObject, JsonValue, as_number, as_object, as_text


class Question[A](Protocol):
    """System One に送れる1つの質問。"""

    def payload(self) -> JsonObject:
        """リクエストに載せる質問定義。"""
        ...

    def read(self, answer: JsonObject) -> A:
        """応答の1件から、この質問の答えを取り出す。"""
        ...


class Primitive(StrEnum):
    """System One の質問種別。"""

    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


@dataclass(frozen=True)
class NoulQuestion:
    """はい・いいえを問い、はいの確率 0.0〜1.0 を得る質問。"""

    instructions: str

    def payload(self) -> JsonObject:
        return {"type": Primitive.NOUL.value, "instructions": self.instructions}

    def read(self, answer: JsonObject) -> float:
        value = as_number(answer.get(Primitive.NOUL.value), "answers.answer.noul")
        if not 0.0 <= value <= 1.0:
            raise JevApiError("noul が 0.0〜1.0 の範囲外です")
        return value


@dataclass(frozen=True)
class ChoiceQuestion:
    """選択肢から1つを選ばせ、選ばれた選択肢名を得る質問。"""

    instructions: str
    criteria: Mapping[str, str | None]

    def payload(self) -> JsonObject:
        return {
            "type": Primitive.CHOICE.value,
            "instructions": self.instructions,
            "criteria": dict(self.criteria),
        }

    def read(self, answer: JsonObject) -> str:
        value = as_text(answer.get(Primitive.CHOICE.value), "answers.answer.choice")
        if value not in self.criteria:
            raise JevApiError(f"choice が選択肢にありません: {value}")
        return value


@dataclass(frozen=True)
class ScoreQuestion:
    """順序づけた評価基準に照らし、0〜len(criteria)-1 の評点を得る質問。"""

    instructions: str
    criteria: Sequence[str]

    def payload(self) -> JsonObject:
        return {
            "type": Primitive.SCORE.value,
            "instructions": self.instructions,
            "criteria": list(self.criteria),
        }

    def read(self, answer: JsonObject) -> float:
        value = as_number(answer.get(Primitive.SCORE.value), "answers.answer.score")
        if not 0.0 <= value <= len(self.criteria) - 1:
            raise JevApiError("score が評価基準の範囲外です")
        return value


ANSWER_KEY = "answer"


def build_request(model: str, state: JsonValue, question: Question[object]) -> JsonObject:
    """1つの質問を含む System One リクエストの本文を組み立てる。"""
    return {
        "model": model,
        "state": state,
        "questions": {ANSWER_KEY: question.payload()},
    }


def read_response[A](response: JsonValue, question: Question[A]) -> A:
    """System One の応答から、質問の種別に応じた答えを取り出す。"""
    answers = as_object(as_object(response, "応答").get("answers"), "answers")
    answer = as_object(answers.get(ANSWER_KEY), f"answers.{ANSWER_KEY}")
    return question.read(answer)
