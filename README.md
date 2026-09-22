# jevmock

関数の本体を書かずに、名前と型注釈から [Jev (TypeSafe System One)](https://docs.typesafe.ai/) に判断を委譲する実験です。

```python
from jevmock import jevmock

@jevmock()
def is_odd(x: int) -> bool:
    """整数が奇数なら真。"""

is_odd(3)  # True
```

デコレータは関数名、docstring、シグネチャから質問文を作り、呼び出し引数を state として
`https://api.typesafe.ai/v1/systemone` に送ります。関数本体は実行されません。

## 戻り値の型と質問の対応

| 戻り値の型注釈 | 追加の指定 | 質問の種別 | 返る値 |
| --- | --- | --- | --- |
| `bool` | なし | noul | 確率が 0.5 以上なら `True` |
| `Enum` のサブクラス | なし | choice | メンバー名で選ばせ、メンバーを返す |
| `Literal[...]` | なし | choice | 選ばれたリテラル値 |
| `str` | `choice=[...]` | choice | 選ばれた選択肢の文字列 |
| `int` | `score=[...]` | score | 評点を四捨五入した整数 |
| `float` | `score=[...]` | score | 0〜`len(score)-1` の評点 |
| `float` | なし | noul | 0.0〜1.0 の確率そのまま |

`choice` は選択肢名の並び、または選択肢名から説明への対応表を渡せます。`Enum` では
メンバーの値が選択肢の説明になります。`score` の評価基準は2段階以上が必要です。

対応しない型注釈、注釈のない関数、`choice` と `score` の同時指定は、呼び出し時ではなく
デコレート時に `JevSignatureError` になります。

```python
from enum import Enum
from typing import Literal

class Sentiment(Enum):
    POSITIVE = "好意的、満足している"
    NEGATIVE = "否定的、不満である"

@jevmock()
def sentiment_of(text: str) -> Sentiment:
    """レビュー文の感情。"""

@jevmock()
def language_of(text: str) -> Literal["japanese", "english", "other"]:
    """文章の言語。"""

@jevmock(score=["穏やか", "苛立っている", "激怒している"])
def anger_of(text: str) -> int:
    """発言者の怒りの強さ。"""
```

`examples/quickstart.py` に一通りの例があります。

引数は JSON に変換して送ります。JSON にできない値は `str()` の結果になります。

## キャッシュ

`ttl` に秒数を与えると、同じ内容のリクエストに対する答えをメモリに保持します。
キーはリクエスト本文の JSON を SHA-256 にかけたもので、デコレートした関数ごとに
独立して持ちます。引数は束縛してから JSON にするため、`f(3)` と `f(x=3)` と
既定値どおりの明示指定は同じキーになります。JSON にできない値が `str()` になるのも
送信時と同じで、`str()` の結果が等しい別の値は同じキーとして扱われます。

```python
@jevmock(ttl=300)
def is_odd(x: int) -> bool:
    """整数が奇数なら真。"""
```

期限切れの項目は、取り出すときと新しく保持するときに捨てます。件数の上限はありません。
例外になった呼び出しは保持しないので、次の呼び出しでまた送ります。`ttl` を省くと
キャッシュは使わず、0 以下の `ttl` はデコレート時に `JevSignatureError` になります。

## APIキー

環境変数 `JEV_API_KEY`（次に `TYPESAFE_API_KEY`）、続いて `~/.local/bin/env` の順で読みます。
設定ファイルは `export JEV_API_KEY='...'` または `JEV_API_KEY=...` の行だけを読み取り、
シェルとしては実行しません。キーの読み取りは最初の送信時で、デコレート時ではありません。

## 開発

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```

テストは `Transport` プロトコルの差し替えで通信せずに実行します。

```python
@jevmock(transport=FakeTransport([{"noul": 0.97}]))
def is_odd(x: int) -> bool: ...
```

`jevmock` の引数では `model`（既定は `jev-latest`）と `transport` も指定できます。
`HttpTransport(timeout=..., key_file=...)` で通信の設定を変えられます。

本体のない関数を mypy の strict で検査すると `empty-body` の警告が出ます。
利用側では該当モジュールで `disable_error_code = ["empty-body"]` を設定してください。

## 構成

- `client.py` — APIキーの読み取りと HTTP 送信、`Transport` プロトコル
- `questions.py` — noul / choice / score の定義と応答の読み取り
- `signature.py` — 関数シグネチャから質問と復号手順を決める
- `decorator.py` — `@jevmock`
