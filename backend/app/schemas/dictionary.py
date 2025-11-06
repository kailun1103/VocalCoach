from typing import List

from pydantic import BaseModel, Field


class DictionaryRequest(BaseModel):
    """
    字典查詢請求結構
    
    說明:
        定義字典查詢 API 的請求參數。
        前端使用 DictionaryRequest，結構完全相同。
    """
    word: str = Field(..., description="學習者選擇的目標單字")
    model: str | None = Field(
        default=None,
        description="可選的覆蓋模型名稱（用於字典查詢）",
    )


class DictionaryResponse(BaseModel):
    """
    字典查詢回應結構
    
    說明:
        定義字典查詢 API 的回應格式。
        前端使用 DictionaryResponse，結構完全相同。
    """
    headword: str = Field(..., description="標準化的字典詞條")
    part_of_speech: str | None = Field(
        default=None,
        description="詞性標籤（例如：名詞、動詞）（若有）",
    )
    definition: str = Field(
        ...,
        description="混合英文意義與繁體中文支援的定義",
    )
    examples: List[str] = Field(
        default_factory=list,
        description="示範用法的例句",
    )
    model: str | None = Field(
        default=None,
        description="LLM 後端實際使用的模型",
    )
