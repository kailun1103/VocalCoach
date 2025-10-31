import base64
import logging
import math
import os
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Optional, Tuple


log = logging.getLogger(__name__)


class TTSService:
    """Service wrapper for Piper text-to-speech synthesis."""

    def __init__(
        self,
        binary_path: Path,
        model_path: Path,
        default_sample_rate: int = 22050,
        use_mock: bool = False,
    ) -> None:
        self.binary_path = binary_path
        self.model_path = model_path
        self.default_sample_rate = default_sample_rate
        self.use_mock = use_mock

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w: Optional[float] = None,
    ) -> Tuple[str, int]:
        if self.use_mock or not self._is_runtime_available():
            return self._mock_audio()

        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="piper_out_"
        ) as tmp_file:
            output_path = Path(tmp_file.name)

        command = [
            str(self.binary_path),
            "--model",
            str(self.model_path),
            "--output_file",
            str(output_path),
        ]

        if voice:
            command.extend(["--speaker", voice])
        if length_scale is not None:
            command.extend(["--length_scale", f"{length_scale:.4f}"])
        if noise_scale is not None:
            command.extend(["--noise_scale", f"{noise_scale:.4f}"])
        if noise_w is not None:
            command.extend(["--noise_w", f"{noise_w:.4f}"])

        log.debug("Executing Piper command: %s", " ".join(command))
        try:
            subprocess.run(
                command,
                input=text,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            log.exception("Piper synthesis failed: %s", exc.stderr)
            raise RuntimeError("Text-to-speech synthesis failed") from exc

        audio_bytes = output_path.read_bytes()
        try:
            with wave.open(str(output_path), "rb") as wav_file:
                sample_rate = wav_file.getframerate()
        finally:
            try:
                os.remove(output_path)
            except OSError:
                log.warning("Failed to remove temporary Piper output: %s", output_path)

        encoded = base64.b64encode(audio_bytes).decode("ascii")
        return encoded, sample_rate

    def _is_runtime_available(self) -> bool:
        return self.binary_path.exists() and self.model_path.exists()

    def _mock_audio(self) -> Tuple[str, int]:
        """Generate a short tone so that the pipeline remains testable without Piper."""
        log.warning("Using mock TTS audio. Verify Piper binary and model paths.")
        duration_seconds = 0.5
        sample_rate = self.default_sample_rate
        frequency = 440.0  # A4 reference tone

        total_samples = int(duration_seconds * sample_rate)
        buffer = bytearray()
        for n in range(total_samples):
            sample = int(
                32767
                * math.sin(2 * math.pi * frequency * (n / sample_rate))
            )
            buffer.extend(struct.pack("<h", sample))

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(buffer)

        audio_bytes = output_path.read_bytes()
        os.remove(output_path)

        encoded = base64.b64encode(audio_bytes).decode("ascii")
        return encoded, sample_rate
