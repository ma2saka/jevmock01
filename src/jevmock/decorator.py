"""関数本体の代わりに Jev の判断を返すデコレータ。"""

import functools
from collections.abc import Callable, Sequence
from typing import ParamSpec, TypeVar, cast

from .client import DEFAULT_MODEL, HttpTransport, Transport
from .questions import build_request
from .signature import Choices, build_spec

P = ParamSpec("P")
R = TypeVar("R")

_default_transport = HttpTransport()


def jevmock(
    *,
    choice: Choices | None = None,
    score: Sequence[str] | None = None,
    model: str = DEFAULT_MODEL,
    transport: Transport | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """関数名と型注釈から質問を組み立て、本体の代わりに Jev の答えを返す。

    戻り値の型注釈で質問の種別が決まる。bool は noul、Enum と Literal は choice、
    str は choice 指定との組み合わせ、int と float は score 指定との組み合わせで
    評点を返し、score のない float は noul の確率をそのまま返す。
    """

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        spec = build_spec(func, choice, score)
        sender = transport or _default_transport

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            request = build_request(model, spec.state(args, kwargs), spec.question)
            return cast(R, spec.answer(sender.ask(request)))

        return wrapper

    return decorate
