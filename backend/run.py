"""Convenience launcher for the API server."""

import sys

import uvicorn

from app.config import get_settings
from app.db_guard import DatabaseConfigError, ProductionConfigError


def main() -> None:
    try:
        s = get_settings()
    except (DatabaseConfigError, ProductionConfigError) as exc:
        print(f"Startup blocked: {exc}", file=sys.stderr)
        sys.exit(1)

    uvicorn.run("app.main:app", host=s.backend_host, port=s.backend_port, reload=True)


if __name__ == "__main__":
    main()
