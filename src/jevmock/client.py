"""Jev API への送信と、APIキーの読み取り。"""

import json
import os
import shlex
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .errors import JevApiError
from .json_value import JsonObject, JsonValue

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT = 30.0
KEY_NAMES = ("JEV_API_KEY", "TYPESAFE_API_KEY")
DEFAULT_KEY_FILE = Path("~/.local/bin/env")


def read_key_file(path: Path) -> dict[str, str]:
    """環境変数形式のファイルから、APIキーの割り当てだけを読み取る。"""
    try:
        lines = path.expanduser().read_text(encoding="utf-8").splitlines()
    except OSError:
        raise JevApiError(f"設定ファイルを読めません: {path}") from None
    values: dict[str, str] = {}
    for line in lines:
        text = line.strip().removeprefix("export ").lstrip()
        name, separator, value = text.partition("=")
        if not separator or name.strip() not in KEY_NAMES:
            continue
        try:
            parts = shlex.split(value, comments=True)
        except ValueError:
            raise JevApiError("APIキー設定の引用符を確認してください") from None
        if len(parts) == 1 and parts[0].strip():
            values[name.strip()] = parts[0].strip()
    return values


def load_api_key(path: Path = DEFAULT_KEY_FILE) -> str:
    """環境変数、次に設定ファイルの順で APIキーを探す。"""
    for name in KEY_NAMES:
        if os.environ.get(name, "").strip():
            return os.environ[name].strip()
    values = read_key_file(path)
    for name in KEY_NAMES:
        if name in values:
            return values[name]
    raise JevApiError("JEV_API_KEY が設定されていません")


class Transport(Protocol):
    """System One のリクエスト本文を送り、応答の JSON を返す。"""

    def ask(self, request: JsonObject) -> JsonValue: ...


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


@dataclass
class HttpTransport:
    """標準ライブラリだけで Jev API を呼ぶ Transport。APIキーは初回送信時に読む。"""

    endpoint: str = ENDPOINT
    timeout: float = DEFAULT_TIMEOUT
    key_file: Path = DEFAULT_KEY_FILE
    _key: str | None = field(default=None, init=False, repr=False)

    def ask(self, request: JsonObject) -> JsonValue:
        if self._key is None:
            self._key = load_api_key(self.key_file)
        body = json.dumps(request, ensure_ascii=False, default=str).encode("utf-8")
        http_request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
            method="POST",
        )
        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(http_request, timeout=self.timeout) as response:
                parsed: JsonValue = json.load(response)
        except urllib.error.HTTPError as exc:
            raise JevApiError(f"Jev API エラー: HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise JevApiError("Jev API に接続できません") from None
        except (ValueError, UnicodeError):
            raise JevApiError("Jev API が不正な JSON を返しました") from None
        return parsed
