"""Convenience launcher for the API server."""

import os
import sys

import uvicorn

from app.config import get_settings
from app.db_guard import DatabaseConfigError, ProductionConfigError


def main() -> None:
    try:
        get_settings()
    except (DatabaseConfigError, ProductionConfigError) as exc:
        print(f"Startup blocked: {exc}", file=sys.stderr)
        sys.exit(1)

    port = int(os.getenv("PORT", "8000"))
    # Render sets PORT — bind publicly and skip reload. Local dev keeps auto-reload.
    is_production_runtime = bool(os.getenv("PORT"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production_runtime,
    )


if __name__ == "__main__":
    main()
