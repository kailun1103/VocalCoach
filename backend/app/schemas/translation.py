from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """
    翻譯請求結構
    
    說明:
        定義翻譯 API 的請求參數。
    """
    text: str = Field(..., description="要翻譯的原始文字")
    target_language: str | None = Field(
        default="zh-TW",
        description="翻譯輸出的 BCP-47 語言標籤；預設為繁體中文",
    )
    model: str | None = Field(
        default=None,
        description="可選的覆蓋模型名稱；回退到配置的翻譯模型",
    )


class TranslationResponse(BaseModel):
    """
    翻譯回應結構
    
    說明:
        定義翻譯 API 的回應格式。
    """
    translated_text: str = Field(..., description="翻譯後的文字輸出")
    model: str | None = Field(
        default=None,
        description="後端用於翻譯的模型名稱",
    )
