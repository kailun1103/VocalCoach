"""
FastAPI 應用程式主入口

此模組建立並配置 FastAPI 應用程式實例，註冊所有 API 路由，
並可選擇性地掛載前端靜態檔案。
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import register_routes
from .core import configure_logging

# 配置日誌系統
configure_logging()

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="EnglishTalk API",
    version="0.1.0",
    description="語音處理端點與本地大型語言模型的聊天代理服務",
)

# 註冊所有 API 路由
register_routes(app)


def _attach_frontend(app: FastAPI) -> None:
    """
    掛載前端靜態檔案（如果存在）
    
    參數:
        app: FastAPI 應用程式實例
    
    說明:
        此函數會嘗試找到並掛載已編譯的前端檔案。
        如果前端檔案不存在或掛載失敗，不會影響 API 的正常運作。
    """
    try:
        # 找到專案根目錄
        root_dir = Path(__file__).resolve().parents[2]
        dist_dir = root_dir / "frontend" / "dist"
        
        # 確認前端編譯目錄是否存在
        if not dist_dir.exists():
            return

        # 掛載靜態檔案目錄
        app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="app")

        # 提供前端入口點
        @app.get("/app", include_in_schema=False)  # type: ignore
        async def app_index() -> FileResponse:
            """返回前端應用程式的 index.html"""
            return FileResponse(str(dist_dir / "index.html"))
            
    except Exception:
        # 防禦性處理：如果掛載失敗，不影響 API 運作
        return


# 執行前端檔案掛載
_attach_frontend(app)
