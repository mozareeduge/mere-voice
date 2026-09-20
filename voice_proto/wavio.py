from __future__ import annotations

import wave
from pathlib import Path
import numpy as np


def read_wav(path: Path):
    with wave.open(str(path), "rb") as w:
        channels = w.getnchannels()
        sample_rate = w.getframerate()
        width = w.getsampwidth()
        frames = w.getnframes()
        raw = w.readframes(frames)
    if width != 2:
        raise ValueError(f"Only 16-bit PCM WAV is supported by fallback mixer: {path}")
    audio = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).T
    else:
        audio = audio.reshape(1, -1)
    return audio, sample_rate


def write_wav(path: Path, audio: np.ndarray, sample_rate: int):
    path.parent.mkdir(parents=True, exist_ok=True)
    if audio.ndim == 1:
        audio = audio.reshape(1, -1)
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio.T.reshape(-1) * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(audio.shape[0])
        w.setsampwidth(2)
        w.setframerate(int(sample_rate))
        w.writeframes(pcm)


def duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as w:
        return round(w.getnframes() * 1000 / w.getframerate())
