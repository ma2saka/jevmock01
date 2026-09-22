"""jevmock が送出する例外。"""


class JevError(Exception):
    """jevmock 共通の基底例外。"""


class JevSignatureError(JevError, TypeError):
    """デコレート対象の関数シグネチャから質問を組み立てられない。"""


class JevApiError(JevError):
    """Jev API への通信、または応答の解釈に失敗した。"""
