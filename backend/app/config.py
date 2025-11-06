"""
向後兼容的配置設定存取點

新的程式碼應優先從 backend.app.core 匯入。
此模組提供了向後兼容性，方便從舊版本遷移。
"""

from .core.config import Settings, settings

__all__ = ["Settings", "settings"]
