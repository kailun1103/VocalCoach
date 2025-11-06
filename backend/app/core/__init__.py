"""
核心應用程式設施模組

此模組提供應用程式的核心功能，包括配置管理和日誌系統。
"""

from .config import Settings, settings
from .logging import configure_logging

__all__ = ["Settings", "settings", "configure_logging"]
