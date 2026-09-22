import pytest

from jevmock.client import load_api_key, read_key_file
from jevmock.errors import JevApiError


def test_environment_takes_precedence(monkeypatch, tmp_path):
    path = tmp_path / "env"
    path.write_text("export JEV_API_KEY='from-file'\n", encoding="utf-8")
    monkeypatch.setenv("JEV_API_KEY", "from-env")
    assert load_api_key(path) == "from-env"


def test_reads_key_file(monkeypatch, tmp_path):
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    path = tmp_path / "env"
    path.write_text(
        "# comment\nPATH=/usr/bin\nexport TYPESAFE_API_KEY='from-file'\n", encoding="utf-8"
    )
    assert read_key_file(path) == {"TYPESAFE_API_KEY": "from-file"}
    assert load_api_key(path) == "from-file"


def test_missing_key(monkeypatch, tmp_path):
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    path = tmp_path / "env"
    path.write_text("PATH=/usr/bin\n", encoding="utf-8")
    with pytest.raises(JevApiError):
        load_api_key(path)
    with pytest.raises(JevApiError):
        load_api_key(tmp_path / "missing")
