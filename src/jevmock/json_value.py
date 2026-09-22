"""JSON 値の型と、型を確かめながら読み取る補助関数。"""

from collections.abc import Mapping, Sequence

from .errors import JevApiError

type JsonValue = None | bool | int | float | str | Sequence["JsonValue"] | Mapping[str, "JsonValue"]
type JsonObject = Mapping[str, JsonValue]


def as_object(value: JsonValue, where: str) -> JsonObject:
    """JSON オブジェクトとして読む。オブジェクトでなければ JevApiError。"""
    if not isinstance(value, Mapping):
        raise JevApiError(f"{where} がオブジェクトではありません")
    return value


def as_number(value: JsonValue, where: str) -> float:
    """真偽値を除く数値として読む。数値でなければ JevApiError。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise JevApiError(f"{where} が数値ではありません")
    return float(value)


def as_text(value: JsonValue, where: str) -> str:
    """文字列として読む。文字列でなければ JevApiError。"""
    if not isinstance(value, str):
        raise JevApiError(f"{where} が文字列ではありません")
    return value
