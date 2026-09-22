"""System One の答えを一定時間だけ保持する素朴なメモリキャッシュ。"""

import hashlib
from dataclasses import dataclass, field
from time import monotonic

from .json_value import JsonObject, to_json_bytes


def request_key(request: JsonObject) -> str:
    """リクエスト本文の JSON 表現から、キャッシュのキーを作る。"""
    return hashlib.sha256(to_json_bytes(request)).hexdigest()


MISS = object()
"""キャッシュに値がないことを表す番兵。"""


@dataclass
class TtlCache:
    """キーごとに値を保持し、ttl 秒を過ぎたものは取り出せなくなるキャッシュ。"""

    ttl: float
    _entries: dict[str, tuple[float, object]] = field(default_factory=dict, init=False, repr=False)

    def get(self, key: str, default: object = MISS) -> object:
        """期限内の値を返す。期限切れと未登録では default を返す。"""
        entry = self._entries.get(key)
        if entry is None:
            return default
        expires_at, value = entry
        if expires_at <= monotonic():
            del self._entries[key]
            return default
        return value

    def set(self, key: str, value: object) -> None:
        """値を ttl 秒後まで有効なものとして保持し、期限切れの項目を捨てる。"""
        now = monotonic()
        self._entries = {k: e for k, e in self._entries.items() if e[0] > now}
        self._entries[key] = (now + self.ttl, value)
