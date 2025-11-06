"""
日誌配置模組

此模組提供應用程式的日誌系統配置功能。
"""

import logging
from typing import Literal, Optional


def configure_logging(
    level: Optional[int | Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]] = None
) -> None:
    """
    配置應用程式的根日誌記錄器
    
    參數:
        level: 日誌級別，可以是整數或字串（如 "DEBUG", "INFO" 等）
               如果未指定，預設為 INFO 級別
    
    說明:
        FastAPI/Uvicorn 通常會自動配置日誌，但在直接執行
        `python -m backend.app.main` 或執行單元測試時，
        需要手動配置以確保日誌輸出的一致性。
    """
    # 如果 level 是字串，轉換為對應的日誌級別常數
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # 配置基本日誌設定
    logging.basicConfig(level=level or logging.INFO)
