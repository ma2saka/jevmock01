"""jevmock の使い方を一通り示す。実行には Jev の APIキーが必要。"""

from enum import Enum
from typing import Literal

from jevmock import jevmock


@jevmock()
def is_odd(x: int) -> bool:
    """整数が奇数なら真。"""

@jevmock()
def language_of(text: str) -> Literal["japanese", "english", "other"]:
    """文章の言語。"""

class Sentiment(Enum):
    POSITIVE = "好意的、満足している"
    NEGATIVE = "否定的、不満である"

@jevmock()
def sentiment_of(text: str) -> Sentiment:
    """レビュー文の感情。"""

@jevmock(score=["穏やか", "苛立っている", "激怒している"])
def anger_of(text: str) -> int:
    """発言者の怒りの強さ。"""

print("is_odd(3) =", is_odd(3))
print("is_odd(4) =", is_odd(4))
print("language_of =", language_of("今日はいい天気ですね"))
print("sentiment_of =", sentiment_of("二度と使いたくない"))
print("anger_of =", anger_of("ふざけるな、金を返せ"))
print("anger_of =", anger_of("今日はいい天気ですね"))
