"""
語音轉文字服務模組

此模組提供基於 Whisper.cpp 的語音轉文字功能封裝。
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


log = logging.getLogger(__name__)


class STTService:
    """
    Whisper.cpp 語音轉文字服務封裝類別
    
    此類別提供語音轉文字推理功能，使用 Whisper.cpp 引擎。
    """

    def __init__(
        self,
        binary_path: Path,
        model_path: Path,
        language: str = "en",
        use_mock: bool = False,
        threads: int = 1,
        beam_size: int = 1,
        best_of: int = 1,
        temperature: float = 0.0,
        print_timestamps: bool = False,
    ) -> None:
        """
        初始化語音轉文字服務
        
        參數:
            binary_path: Whisper.cpp 可執行檔路徑
            model_path: Whisper 模型檔案路徑
            language: 語言代碼（預設為 "en"）
            use_mock: 是否使用模擬模式
            threads: CPU 執行緒數量
            beam_size: Beam search 大小
            best_of: 保留的最佳候選數量
            temperature: 取樣溫度
            print_timestamps: 是否輸出時間戳記
        """
        self.binary_path = binary_path
        self.model_path = model_path
        self.language = language
        self.use_mock = use_mock
        self.threads = max(1, threads)  # 確保至少有 1 個執行緒
        self.beam_size = max(1, beam_size)  # 確保 beam_size 至少為 1
        self.best_of = max(1, best_of)  # 確保 best_of 至少為 1
        self.temperature = max(0.0, temperature)  # 確保溫度不為負值
        self.print_timestamps = print_timestamps

    def transcribe(self, audio_path: Path) -> str:
        """
        使用 Whisper.cpp 將音訊檔案轉寫為文字
        
        參數:
            audio_path: 要轉寫的音訊檔案路徑
            
        返回:
            str: 轉寫後的文字內容
            
        異常:
            RuntimeError: 當語音轉文字推理失敗時拋出
        """
        # 如果使用模擬模式或執行環境不可用，返回模擬轉寫
        if self.use_mock or not self._is_runtime_available():
            return self._mock_transcription(audio_path)

        # 使用臨時目錄處理 Whisper 輸出
        with tempfile.TemporaryDirectory(prefix="whisper_tmp_") as tmp_dir:
            # Whisper 會將輸出寫入指定前綴的旁邊，我們之後會清理
            output_prefix = Path(tmp_dir) / "transcription"
            
            # 構建 Whisper 命令列參數
            command = [
                str(self.binary_path),
                "-m", str(self.model_path),  # 模型路徑
                "-f", str(audio_path),  # 音訊檔案
                "-otxt",  # 輸出文字格式
                "-of", str(output_prefix),  # 輸出檔案前綴
                "-l", self.language,  # 語言設定
            ]
            
            # 添加進階參數
            command.extend(["--threads", str(self.threads)])
            command.extend(["--beam-size", str(self.beam_size)])
            command.extend(["--best-of", str(self.best_of)])
            command.extend(["--temperature", f"{self.temperature:.2f}"])
            
            if not self.print_timestamps:
                command.append("--no-timestamps")
            command.append("--no-fallback")
            
            log.debug("執行 whisper.cpp 命令: %s", " ".join(command))
            
            try:
                # 執行 Whisper 命令
                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                
                # 讀取轉寫結果
                transcript_path = Path(f"{output_prefix}.txt")
                transcript = transcript_path.read_text(encoding="utf-8").strip()
                return transcript
                
            except subprocess.CalledProcessError as exc:
                log.exception("whisper.cpp 執行失敗: %s", exc.stderr.decode())
                raise RuntimeError("語音轉文字推理失敗") from exc

    def _is_runtime_available(self) -> bool:
        """
        檢查 Whisper 執行環境是否可用
        
        返回:
            bool: 當 Whisper 執行檔和模型檔案都存在時返回 True
        """
        return self.binary_path.exists() and self.model_path.exists()

    def _mock_transcription(self, audio_path: Optional[Path]) -> str:
        """
        返回用於模擬的預設轉寫文字
        
        參數:
            audio_path: 音訊檔案路徑（可選）
            
        返回:
            str: 模擬的轉寫文字
            
        說明:
            當 Whisper 執行環境不可用時，返回確定性的佔位文字。
        """
        log.warning(
            "使用模擬轉寫。請驗證 whisper.cpp 執行檔和模型路徑。"
        )
        placeholder = audio_path.name if audio_path else "audio"
        return f"[模擬轉寫] 偵測到來自 {placeholder} 的語音"
