"""
Backward-compatible access point for configuration settings.

New code should prefer importing from backend.app.core.
"""

from .core.config import Settings, settings

__all__ = ["Settings", "settings"]
