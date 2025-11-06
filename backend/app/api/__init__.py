"""
API 路由註冊模組

此模組負責將所有 API 路由器註冊到 FastAPI 應用程式中。
"""

from fastapi import FastAPI

from .routes import chat, dictionary, grammar, speech, translation


def register_routes(app: FastAPI) -> None:
    """
    將 API 路由器附加到 FastAPI 應用程式
    
    參數:
        app: FastAPI 應用程式實例
    
    說明:
        此函數按照邏輯順序註冊所有的 API 路由器，
        包括語音處理、聊天、字典查詢、文法檢查和翻譯功能。
    """
    # 註冊核心功能路由
    app.include_router(speech.router)
    app.include_router(chat.router)
    app.include_router(dictionary.router)
    app.include_router(grammar.router)
    app.include_router(translation.router)


__all__ = ["register_routes"]
