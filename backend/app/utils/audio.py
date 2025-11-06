"""
音訊處理工具模組

此模組提供音訊檔案的儲存和編解碼功能。
"""

import base64
import time
from pathlib import Path


def save_audio_bytes(audio_dir: Path, audio_bytes: bytes, suffix: str = ".wav") -> Path:
    """
    將原始音訊位元組資料持久化到指定目錄
    
    參數:
        audio_dir: 音訊檔案儲存目錄
        audio_bytes: 原始音訊位元組資料
        suffix: 檔案副檔名（預設為 ".wav"）
    
    返回:
        Path: 儲存的音訊檔案路徑
    
    說明:
        檔案名稱會包含時間戳記以便追蹤。
        呼叫者可以在使用後刪除檔案（例如用於 STT 的臨時檔案）。
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    target_path = audio_dir / f"{timestamp}{suffix}"
    target_path.write_bytes(audio_bytes)
    return target_path


def decode_audio_base64(data: str) -> bytes:
    """
    將 Base64 編碼的音訊資料解碼為原始位元組
    
    參數:
        data: Base64 編碼的音訊字串
    
    返回:
        bytes: 解碼後的原始音訊位元組資料
    """
    return base64.b64decode(data.encode("ascii"))
