from typing import Optional

from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """
    語音轉文字回應結構
    
    說明:
        此類別定義 STT (Speech-to-Text) API 的回應格式。
        前端使用 STTResponse 作為別名，結構完全相同。
    """
    text: str = Field(..., description="轉寫的文字內容")
    duration_ms: float = Field(
        ..., description="處理轉寫請求的總耗時（毫秒）"
    )


class TextToSpeechRequest(BaseModel):
    """
    文字轉語音請求結構
    
    說明:
        定義 TTS (Text-to-Speech) API 的請求參數。
        前端使用 TTSRequest 作為別名，結構完全相同。
    """
    text: str = Field(..., description="要轉換的文字內容")
    voice: str | None = Field(
        default=None,
        description="可選的語音識別碼（用於多人聲音模型）",
    )
    length_scale: float | None = Field(
        default=None,
        ge=0.1,
        description="韻律控制：>1 減慢語速，<1 加快語速",
    )
    noise_scale: float | None = Field(
        default=None,
        ge=0.0,
        description="控制語音能量變化；較低值更平穩",
    )
    noise_w: float | None = Field(
        default=None,
        ge=0.0,
        description="控制音素寬度變化；較高值更富表現力",
    )


class TextToSpeechResponse(BaseModel):
    """
    文字轉語音回應結構
    
    說明:
        定義 TTS API 的回應格式。
        前端使用 TTSResponse 作為別名，結構完全相同。
    """
    audio_base64: str = Field(..., description="Base64 編碼的音訊資料")
    sample_rate: int = Field(..., description="音訊取樣率（Hz）")
    duration_seconds: float = Field(
        ..., description="生成語音音訊的總耗時（秒）"
    )
    voice: str | None = Field(
        default=None,
        description="合成時使用的語音識別碼",
    )
    length_scale: float | None = Field(
        default=None,
        description="合成時應用的韻律 length_scale 值",
    )
    noise_scale: float | None = Field(
        default=None,
        description="合成時應用的韻律 noise_scale 值",
    )
    noise_w: float | None = Field(
        default=None,
        description="合成時應用的韻律 noise_w 值",
    )
