from pydantic import BaseModel, Field


class GrammarCheckRequest(BaseModel):
    """
    文法檢查請求結構
    
    說明:
        定義文法檢查 API 的請求參數。
        前端使用 GrammarCheckRequest，結構完全相同。
    """
    text: str = Field(..., description="要評估文法正確性的文字")
    model: str | None = Field(
        default=None,
        description="可選的覆蓋模型名稱（用於文法檢查）",
    )


class GrammarCheckResponse(BaseModel):
    """
    文法檢查回應結構
    
    說明:
        定義文法檢查 API 的回應格式。
        前端使用 GrammarCheckResponse，結構完全相同。
    """
    is_correct: bool = Field(..., description="指示原始文字是否文法正確")
    feedback: str = Field(..., description="關於問題的說明或正確性確認")
    suggestion: str | None = Field(
        default=None,
        description="適用時提供的文字修正建議",
    )
    model: str | None = Field(
        default=None,
        description="後端用於文法檢查的模型名稱",
    )
