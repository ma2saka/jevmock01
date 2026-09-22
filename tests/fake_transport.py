"""テスト用の Transport 実装。"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from jevmock.json_value import JsonObject, JsonValue, as_object
from jevmock.questions import ANSWER_KEY


@dataclass
class FakeTransport:
    """あらかじめ用意した答えを順に返し、送ったリクエストを記録する。"""

    answers: Sequence[JsonObject]
    requests: list[JsonObject] = field(default_factory=list)

    def ask(self, request: JsonObject) -> JsonValue:
        self.requests.append(request)
        return {"answers": {ANSWER_KEY: self.answers[len(self.requests) - 1]}}


def asked(transport: "FakeTransport", index: int = 0) -> JsonObject:
    """記録したリクエストから、送った質問の定義を取り出す。"""
    questions = as_object(transport.requests[index]["questions"], "questions")
    return as_object(questions[ANSWER_KEY], ANSWER_KEY)
