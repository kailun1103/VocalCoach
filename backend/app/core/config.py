"""
應用程式配置模組

此模組定義了所有應用程式的配置設定，包括語音辨識、文字轉語音、
大型語言模型等服務的配置參數。所有設定都可透過環境變數覆蓋。
"""

from pathlib import Path
import os

from pydantic import Field
from pydantic_settings import BaseSettings

# 定義重要的目錄路徑常數
_APP_DIR = Path(__file__).resolve().parent.parent  # 應用程式根目錄
_MODEL_DIR = _APP_DIR / "model"  # 模型檔案目錄
_STT_DIR = _MODEL_DIR / "stt"  # 語音轉文字模型目錄
_TTS_DIR = _MODEL_DIR / "tts"  # 文字轉語音模型目錄
_TTS_RUNTIME_DIR = _TTS_DIR / "runtime"  # TTS 執行環境目錄
_TTS_VOICES_DIR = _TTS_DIR / "voices"  # TTS 語音模型目錄


def _default_whisper_binary() -> Path:
    """
    尋找 Whisper.cpp 可執行檔
    
    優先使用本地編譯的版本（位於 backend/app/model）。
    返回最可能的候選檔案，部署時可透過環境變數覆蓋。
    
    返回:
        Path: Whisper 可執行檔的路徑
    """
    # 按優先順序搜尋可能的執行檔名稱
    for candidate in ("whisper-cli.exe", "main.exe", "whisper-cli", "main"):
        binary_path = _STT_DIR / candidate
        if binary_path.exists():
            return binary_path
    
    # 如果都找不到，返回預設路徑
    return _STT_DIR / "whisper-cli.exe"


def _default_whisper_model() -> Path:
    """
    返回預設的 Whisper 模型路徑
    
    返回:
        Path: 預設使用的 ggml-small.en-q5_1.bin 模型路徑
    """
    return _STT_DIR / "ggml-small.en-q5_1.bin"


class Settings(BaseSettings):
    """
    應用程式配置設定類別
    
    從環境變數或預設值載入配置。所有設定都可透過 .env 檔案或
    環境變數進行覆蓋。
    """

    # ========== Whisper.cpp 語音轉文字設定 ==========
    whisper_binary: Path = Field(
        default_factory=_default_whisper_binary,
        description="Whisper.cpp 可執行檔路徑",
    )
    whisper_model: Path = Field(
        default_factory=_default_whisper_model,
        description="Whisper.cpp 模型檔案路徑",
    )
    whisper_threads: int = Field(
        default_factory=lambda: os.cpu_count() or 1,
        description="分配給 Whisper.cpp 的 CPU 執行緒數量",
    )
    whisper_beam_size: int = Field(
        default=1,
        description="解碼時的 beam search 大小（數值越大品質越好但速度越慢）",
    )
    whisper_best_of: int = Field(
        default=1,
        description="保留的最佳候選數量（數值越大品質越好但速度越慢）",
    )
    whisper_temperature: float = Field(
        default=0.0,
        description="Whisper.cpp 解碼的取樣溫度",
    )
    whisper_print_timestamps: bool = Field(
        default=False,
        description="是否在轉寫輸出中包含時間戳記",
    )
    # ========== Piper 文字轉語音設定 ==========
    piper_binary: Path = Field(
        default=_TTS_RUNTIME_DIR / "piper.exe",
        description="Piper 可執行檔路徑",
    )
    piper_model: Path = Field(
        default=_TTS_VOICES_DIR / "en_US-amy-medium.onnx",
        description="Piper 語音模型路徑",
    )
    
    # ========== 一般設定 ==========
    data_directory: Path = Field(
        default=Path("./data"),
        description="API 生成的持久化音訊檔案的基礎目錄",
    )
    use_mock_services: bool = Field(
        default=False,
        description="當模型不可用時，是否切換為模擬實作",
    )
    mock_language: str = Field(
        default="en",
        description="模擬資料生成時使用的預設語言代碼",
    )

    # ========== LLM（OpenAI 相容）端點設定 ==========
    llm_base_url: str = Field(
        default="http://127.0.0.1:1234/v1",
        description="本地 OpenAI 相容 LLM 伺服器的基礎 URL",
    )
    llm_default_model: str | None = Field(
        default=None,
        description="預設聊天模型名稱（請求可覆蓋此設定）",
    )
    llm_default_temperature: float = Field(
        default=0.0,
        description="當聊天請求未指定時使用的備用溫度值",
    )
    llm_system_prompt: str | None = Field(
        default=(
            "你是一位友善的英語母語者，正在幫助中文初學者練習英語口說。"
            "請嚴格遵守以下規則："
            "1) 每次回覆限制在 2 到 3 句話內，保持簡短清晰。"
            "2) 總是展開縮寫（例如寫 do not 而不是 don't）。"
            "3) 使用簡單的詞彙和自然的語氣，適當使用逗號來分隔語句。"
            "4) 可以使用逗號（,）、句號（.）、問號（?）和驚嘆號（!），但絕不包含引號、表情符號、項目符號、編號列表或特殊符號（# * / % -）。"
            "5) 適當時用簡短的鼓勵語句（如 Good job 或 Keep going）。"
        ),
        description="適合 TTS 的簡短系統提示，限制在 2-3 句話內回覆",
    )
    llm_response_word_min: int = Field(
        default=5,
        description="助手回覆中要求的最小單字數（適合 2-3 句話）",
    )
    llm_response_word_max: int = Field(
        default=15,
        description="助手回覆中允許的最大單字數（適合 2-3 句話）",
    )
    llm_response_retry_attempts: int = Field(
        default=2,
        description="在退回到修剪之前，要求 LLM 修正規則違反的額外嘗試次數",
    )
    # ========== 翻譯服務設定 ==========
    llm_translation_model: str | None = Field(
        default=None,
        description="翻譯請求使用的可選覆蓋模型名稱",
    )
    llm_translation_prompt: str = Field(
        default=(
            "你是一位翻譯大師。請將使用者的訊息翻譯成 {target_language}。"
            "只返回翻譯後的文字，不要加入額外的評論。"
        ),
        description="翻譯請求使用的系統提示範本",
    )
    
    # ========== 文法檢查服務設定 ==========
    llm_grammar_model: str | None = Field(
        default=None,
        description="文法檢查請求使用的可選覆蓋模型名稱",
    )
    llm_grammar_prompt: str = Field(
        default=(
            "你是一位英語文法專家，也是中文學習者的耐心導師。"
            "請根據美式英語標準，檢查使用者輸入的句子或段落的文法、標點符號和大小寫準確性。"
            "請嚴格以 JSON 格式回應，使用以下鍵值："
            "\"is_correct\"（布林值），"
            "\"feedback\"（繁體中文解釋，描述問題及如何改進），"
            "\"suggestion\"（完整修正的英文句子，不含引號）。"
            "所有自然語言必須使用繁體中文撰寫。"
            "不要在 JSON 物件外包含任何文字。"
        ),
        description="文法檢查請求使用的系統提示，為中文學習者提供簡潔的教學回饋",
    )

    # ========== 字典查詢服務設定 ==========
    llm_dictionary_model: str | None = Field(
        default=None,
        description="字典查詢使用的可選覆蓋模型名稱",
    )
    llm_dictionary_prompt: str = Field(
        default=(
            '你是一位英語學習助手。使用者將提供包含 "word" 鍵的 JSON。'
            '返回一個 JSON 物件，包含以下鍵值：'
            '"headword"（字串）、'
            '"part_of_speech"（**只包含詞性的繁體中文和英文**，格式嚴格為「中文詞性 英文詞性」，例如「動詞 verb」、「名詞 noun」、「形容詞 adjective」、「副詞 adverb」。絕對不可包含單字的意思或定義，只能是詞性類別）、'
            '"definition"（**僅使用繁體中文**的簡潔定義說明，不要包含英文）、'
            '"examples"（2 個例句的陣列，**每個例句必須包含查詢的單字**。每個例句的格式必須是：「英文句子\\n中文翻譯」，使用換行符號 \\n 分隔英文和繁體中文翻譯）。'
            '**part_of_speech 錯誤範例**："練習動詞 verb"（錯誤，包含了單字意思）、"practicing verb"（錯誤，包含了單字本身）。'
            '**part_of_speech 正確範例**："動詞 verb"、"名詞 noun"、"形容詞 adjective"。'
            '**重要：definition 必須只使用繁體中文（Traditional Chinese），絕對不可使用簡體中文或英文。**'
            'examples 必須提供 2 個例句，每個例句格式為「英文\\n中文」，不可超過 2 個。'
            '範例格式：["I love reading books.\\n我喜歡閱讀書籍。", "She reads every day.\\n她每天都閱讀。"]'
            '不要在 JSON 物件外輸出任何內容。'
        ),
        description="用於情境字典解釋的系統提示，例句包含英文和中文翻譯",
    )

    class Config:
        """Pydantic 配置類別"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# 建立全域設定實例
settings = Settings()
