"""
Audio utilities for voice processing
"""
import base64
import io
from typing import Tuple, Optional


def encode_audio_to_base64(audio_bytes: bytes) -> str:
    """Convert audio bytes to base64 string."""
    return base64.b64encode(audio_bytes).decode('utf-8')


def decode_base64_to_audio(base64_string: str) -> bytes:
    """Convert base64 string to audio bytes."""
    return base64.b64decode(base64_string)


def get_audio_format(mime_type: str) -> Tuple[int, int, int]:
    """
    Get audio format parameters from MIME type.
    
    Returns:
        Tuple of (sample_rate, channels, bits_per_sample)
    """
    formats = {
        "audio/pcm": (16000, 1, 16),
        "audio/wav": (16000, 1, 16),
        "audio/webm": (48000, 1, 16),
        "audio/ogg": (48000, 1, 16),
        "audio/mp3": (44100, 2, 16),
    }
    return formats.get(mime_type, (16000, 1, 16))


def normalize_audio(audio_bytes: bytes, target_sample_rate: int = 16000) -> bytes:
    """
    Normalize audio to target sample rate.
    
    Note: This is a placeholder. For production, use scipy or librosa.
    """
    # In production, use scipy.signal.resample or librosa
    return audio_bytes
