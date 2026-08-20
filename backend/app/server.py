import os
from typing import Any

import uvicorn


def create_server(
    application: Any = "app.main:app",
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> uvicorn.Server:
    config = uvicorn.Config(
        application,
        host=host,
        port=port,
        proxy_headers=False,
    )
    return uvicorn.Server(config)


def run() -> None:
    port = int(os.environ.get("PORT", "8000"))
    create_server(port=port).run()


if __name__ == "__main__":
    run()
