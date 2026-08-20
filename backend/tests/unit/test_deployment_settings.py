from unittest.mock import Mock, patch

import pytest

from app.server import run
from app.settings import Settings


@pytest.mark.parametrize(
    ("provided", "expected"),
    [
        (
            "postgres://user:password@host/database",
            "postgresql+psycopg://user:password@host/database",
        ),
        (
            "postgresql://user:password@host/database",
            "postgresql+psycopg://user:password@host/database",
        ),
        (
            "postgresql+psycopg://user:password@host/database",
            "postgresql+psycopg://user:password@host/database",
        ),
    ],
)
def test_database_url_uses_psycopg_dialect(provided: str, expected: str) -> None:
    assert Settings(database_url=provided).database_url == expected


def test_server_uses_provider_port(monkeypatch: pytest.MonkeyPatch) -> None:
    server = Mock()
    monkeypatch.setenv("PORT", "10000")

    with patch("app.server.create_server", return_value=server) as create_server:
        run()

    create_server.assert_called_once_with(port=10000)
    server.run.assert_called_once_with()
