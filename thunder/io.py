"""
thunder.io
==========

Audio I/O operations for thunder acoustics pipeline.
"""

import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def load_audio(
    filepath: str | Path,
    sr: Optional[int] = None,
    mono: bool = True,
    dtype: str = "float32",
) -> Tuple[np.ndarray, int]:
    """
    Load audio file.

    Parameters
    ----------
    filepath : str or Path
        Path to audio file
    sr : int, optional
        Target sample rate (None = native rate)
    mono : bool, default=True
        Convert to mono
    dtype : str, default="float32"
        Data type for audio samples

    Returns
    -------
    audio : np.ndarray
        Audio samples, shape (n_samples,) if mono else (n_channels, n_samples)
    sr : int
        Sample rate

    Examples
    --------
    >>> audio, sr = load_audio("thunder.wav", sr=48000)
    >>> print(f"Loaded {len(audio)} samples @ {sr} Hz")
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    logger.info(f"Loading audio: {filepath}")

    try:
        # Use librosa for robust loading with resampling
        audio, sr_loaded = librosa.load(filepath, sr=sr, mono=mono, dtype=dtype)
        logger.info(
            f"Loaded {len(audio)} samples @ {sr_loaded} Hz "
            f"({len(audio) / sr_loaded:.2f} seconds)"
        )
        return audio, sr_loaded
    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise


def save_audio(
    filepath: str | Path,
    audio: np.ndarray,
    sr: int,
    bit_depth: int = 24,
    overwrite: bool = False,
) -> None:
    """
    Save audio to WAV file.

    Parameters
    ----------
    filepath : str or Path
        Output path
    audio : np.ndarray
        Audio samples
    sr : int
        Sample rate
    bit_depth : int, default=24
        Bit depth (16, 24, or 32)
    overwrite : bool, default=False
        Overwrite existing file

    Examples
    --------
    >>> save_audio("output.wav", audio, 48000, bit_depth=24)
    """
    filepath = Path(filepath)
    if filepath.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {filepath}")

    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Map bit depth to soundfile subtype
    subtype_map = {16: "PCM_16", 24: "PCM_24", 32: "PCM_32"}
    subtype = subtype_map.get(bit_depth, "PCM_24")

    logger.info(f"Saving audio: {filepath} ({bit_depth}-bit)")
    sf.write(filepath, audio, sr, subtype=subtype)
    logger.info(f"Saved {len(audio)} samples @ {sr} Hz")


def get_audio_info(filepath: str | Path) -> dict:
    """
    Get audio file metadata.

    Parameters
    ----------
    filepath : str or Path
        Path to audio file

    Returns
    -------
    info : dict
        Metadata dict with keys: sr, channels, duration, frames

    Examples
    --------
    >>> info = get_audio_info("thunder.wav")
    >>> print(f"Duration: {info['duration']:.2f} seconds")
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    info = sf.info(filepath)
    return {
        "sample_rate": info.samplerate,
        "channels": info.channels,
        "duration": info.duration,
        "frames": info.frames,
        "format": info.format,
        "subtype": info.subtype,
    }


def validate_audio(
    audio: np.ndarray, sr: int, min_duration: float = 1.0, max_duration: float = 3600.0
) -> bool:
    """
    Validate audio array.

    Parameters
    ----------
    audio : np.ndarray
        Audio samples
    sr : int
        Sample rate
    min_duration : float, default=1.0
        Minimum duration in seconds
    max_duration : float, default=3600.0
        Maximum duration in seconds (1 hour)

    Returns
    -------
    valid : bool
        True if valid

    Raises
    ------
    ValueError
        If audio is invalid
    """
    if audio.size == 0:
        raise ValueError("Audio array is empty")

    if not np.isfinite(audio).all():
        raise ValueError("Audio contains NaN or Inf values")

    duration = len(audio) / sr
    if duration < min_duration:
        raise ValueError(f"Audio too short: {duration:.2f}s < {min_duration}s")
    if duration > max_duration:
        raise ValueError(f"Audio too long: {duration:.2f}s > {max_duration}s")

    return True
