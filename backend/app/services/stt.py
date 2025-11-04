import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


log = logging.getLogger(__name__)


class STTService:
    """Service wrapper for Whisper.cpp speech-to-text inference."""

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
        self.binary_path = binary_path
        self.model_path = model_path
        self.language = language
        self.use_mock = use_mock
        self.threads = max(1, threads)
        self.beam_size = max(1, beam_size)
        self.best_of = max(1, best_of)
        self.temperature = max(0.0, temperature)
        self.print_timestamps = print_timestamps

    def transcribe(self, audio_path: Path) -> str:
        """Transcribe an audio file into text using whisper.cpp."""
        if self.use_mock or not self._is_runtime_available():
            return self._mock_transcription(audio_path)

        with tempfile.TemporaryDirectory(prefix="whisper_tmp_") as tmp_dir:
            # Whisper writes its outputs next to the provided prefix; we clean them up afterwards.
            output_prefix = Path(tmp_dir) / "transcription"
            command = [
                str(self.binary_path),
                "-m",
                str(self.model_path),
                "-f",
                str(audio_path),
                "-otxt",
                "-of",
                str(output_prefix),
                "-l",
                self.language,
            ]
            command.extend(["--threads", str(self.threads)])
            command.extend(["--beam-size", str(self.beam_size)])
            command.extend(["--best-of", str(self.best_of)])
            command.extend(["--temperature", f"{self.temperature:.2f}"])
            if not self.print_timestamps:
                command.append("--no-timestamps")
            command.append("--no-fallback")
            log.debug("Executing whisper.cpp command: %s", " ".join(command))
            try:
                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                transcript_path = Path(f"{output_prefix}.txt")
                transcript = transcript_path.read_text(encoding="utf-8").strip()
                return transcript
            except subprocess.CalledProcessError as exc:
                log.exception("whisper.cpp execution failed: %s", exc.stderr.decode())
                raise RuntimeError("Speech-to-text inference failed") from exc

    def _is_runtime_available(self) -> bool:
        """Return True when both the whisper binary and model file exist."""
        return self.binary_path.exists() and self.model_path.exists()

    def _mock_transcription(self, audio_path: Optional[Path]) -> str:
        """Return a deterministic placeholder transcription used during mocks."""
        log.warning(
            "Using mock transcription. Verify whisper.cpp binary and model paths."
        )
        placeholder = audio_path.name if audio_path else "audio"
        return f"[mock-transcription] Detected speech from {placeholder}"
