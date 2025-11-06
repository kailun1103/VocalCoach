from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    聊天訊息結構
    
    說明:
        定義單一聊天訊息的格式。
        前端使用 ChatMessage，結構完全相同。
    """
    role: Literal["system", "user", "assistant"] = Field(
        ..., description="聊天角色（依照 OpenAI 類似的 API 規範）"
    )
    content: str = Field(..., description="訊息內容文字")


class ChatRequest(BaseModel):
    """
    聊天請求結構
    
    說明:
        定義聊天 API 的請求參數。
        前端使用 ChatRequest，結構完全相同。
    """
    model: Optional[str] = Field(
        default=None,
        description="模型名稱；省略時使用伺服器預設值",
    )
    messages: List[ChatMessage] = Field(
        default_factory=list, description="按順序排列的對話訊息"
    )
    temperature: float | None = Field(
        default=None, description="轉發給 LLM 的取樣溫度"
    )
    max_tokens: int | None = Field(
        default=None, description="完成的最大 token 數量；可選"
    )


class ChatResponse(BaseModel):
    """
    聊天回應結構
    
    說明:
        定義聊天 API 的回應格式。
        前端使用 ChatResponse，結構完全相同。
    """
    content: str = Field(..., description="助手回覆內容")
    model: str | None = Field(
        default=None, description="後端回報的模型名稱"
    )
    finish_reason: str | None = Field(
        default=None, description="生成停止的原因"
    )
    prompt_tokens: int | None = Field(default=None, description="提示使用的 token 數量")
    completion_tokens: int | None = Field(default=None, description="完成使用的 token 數量")
    total_tokens: int | None = Field(default=None, description="總 token 數量")
