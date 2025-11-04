import logging
from typing import Literal, Optional


def configure_logging(level: Optional[int | Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = None) -> None:
    """
    Configure root logging for the application.

    FastAPI/Uvicorn normally configures logging, but running the app via plain
    `python -m backend.app.main` or during unit tests benefits from a predictable setup.
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=level or logging.INFO)
