import base64
import time
from pathlib import Path


def save_audio_bytes(audio_dir: Path, audio_bytes: bytes, suffix: str = ".wav") -> Path:
    """
    Persist raw audio bytes to the given directory.

    Files are timestamped for traceability. Callers may remove the file afterwards when
    using it as a transient artifact (e.g., for STT).
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    target_path = audio_dir / f"{timestamp}{suffix}"
    target_path.write_bytes(audio_bytes)
    return target_path


def decode_audio_base64(data: str) -> bytes:
    """Decode a base64-encoded audio payload into raw bytes."""
    return base64.b64decode(data.encode("ascii"))
