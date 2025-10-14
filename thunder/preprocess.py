"""
thunder.preprocess
==================

Audio preprocessing: noise reduction, filtering, normalization.
"""

import numpy as np
from scipy import signal
from scipy.signal import butter, sosfilt
import librosa
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def bandpass_filter(
    audio: np.ndarray,
    sr: int,
    low: float = 20.0,
    high: float = 6000.0,
    order: int = 4,
) -> np.ndarray:
    """
    Apply Butterworth bandpass filter.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    low : float, default=20.0
        Low cutoff frequency (Hz)
    high : float, default=6000.0
        High cutoff frequency (Hz)
    order : int, default=4
        Filter order

    Returns
    -------
    filtered : np.ndarray
        Filtered audio

    Examples
    --------
    >>> filtered = bandpass_filter(audio, 48000, low=20, high=6000)
    """
    nyquist = sr / 2
    low_norm = low / nyquist
    high_norm = high / nyquist

    if low_norm <= 0 or high_norm >= 1:
        logger.warning(f"Invalid filter range: {low}-{high} Hz @ {sr} Hz")
        return audio

    sos = butter(order, [low_norm, high_norm], btype="band", output="sos")
    filtered = sosfilt(sos, audio)

    logger.info(f"Bandpass filter: {low}-{high} Hz (order {order})")
    return filtered


def normalize_audio(
    audio: np.ndarray, target_db: float = -20.0, method: str = "rms"
) -> np.ndarray:
    """
    Normalize audio to target level.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    target_db : float, default=-20.0
        Target level in dB
    method : str, default="rms"
        Normalization method: "peak" or "rms"

    Returns
    -------
    normalized : np.ndarray
        Normalized audio

    Examples
    --------
    >>> normalized = normalize_audio(audio, target_db=-20.0)
    """
    if method == "peak":
        peak = np.abs(audio).max()
        if peak == 0:
            return audio
        target_linear = 10 ** (target_db / 20)
        gain = target_linear / peak
    elif method == "rms":
        rms = np.sqrt(np.mean(audio**2))
        if rms == 0:
            return audio
        target_linear = 10 ** (target_db / 20)
        gain = target_linear / rms
    else:
        raise ValueError(f"Unknown normalization method: {method}")

    normalized = audio * gain
    logger.info(f"Normalized to {target_db} dB ({method})")
    return normalized


def reduce_noise_spectral_subtraction(
    audio: np.ndarray,
    sr: int,
    noise_profile_duration: float = 0.5,
    n_fft: int = 2048,
    hop_length: int = 512,
) -> np.ndarray:
    """
    Reduce noise using spectral subtraction.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    noise_profile_duration : float, default=0.5
        Duration of initial silence to use as noise profile (seconds)
    n_fft : int, default=2048
        FFT window size
    hop_length : int, default=512
        Hop length

    Returns
    -------
    denoised : np.ndarray
        Denoised audio

    Examples
    --------
    >>> denoised = reduce_noise_spectral_subtraction(audio, 48000)
    """
    # Extract noise profile from initial silence
    noise_frames = int(noise_profile_duration * sr)
    if noise_frames > len(audio):
        logger.warning("Noise profile duration exceeds audio length. Skipping.")
        return audio

    noise_profile = audio[:noise_frames]

    # STFT
    stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
    noise_stft = librosa.stft(noise_profile, n_fft=n_fft, hop_length=hop_length)

    # Estimate noise power spectrum
    noise_power = np.mean(np.abs(noise_stft) ** 2, axis=1, keepdims=True)

    # Spectral subtraction
    signal_power = np.abs(stft) ** 2
    denoised_power = np.maximum(signal_power - noise_power, 0)
    denoised_magnitude = np.sqrt(denoised_power)

    # Maintain phase
    phase = np.angle(stft)
    denoised_stft = denoised_magnitude * np.exp(1j * phase)

    # Inverse STFT
    denoised = librosa.istft(denoised_stft, hop_length=hop_length, length=len(audio))

    logger.info(f"Noise reduction applied (spectral subtraction)")
    return denoised


def trim_silence(
    audio: np.ndarray,
    sr: int,
    threshold_db: float = -40.0,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Trim leading and trailing silence.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    threshold_db : float, default=-40.0
        Silence threshold in dB
    frame_length : int, default=2048
        Frame length for energy calculation
    hop_length : int, default=512
        Hop length

    Returns
    -------
    trimmed : np.ndarray
        Trimmed audio
    boundaries : tuple of int
        (start_sample, end_sample) of non-silent region

    Examples
    --------
    >>> trimmed, (start, end) = trim_silence(audio, 48000)
    """
    non_silent = librosa.effects.split(
        audio, top_db=-threshold_db, frame_length=frame_length, hop_length=hop_length
    )

    if len(non_silent) == 0:
        logger.warning("No non-silent regions found")
        return audio, (0, len(audio))

    start = non_silent[0][0]
    end = non_silent[-1][1]
    trimmed = audio[start:end]

    logger.info(f"Trimmed silence: {start / sr:.2f}s - {end / sr:.2f}s")
    return trimmed, (start, end)


def preprocess_pipeline(
    audio: np.ndarray,
    sr: int,
    config: dict,
) -> np.ndarray:
    """
    Full preprocessing pipeline.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    config : dict
        Configuration dict with keys:
        - bandpass: {low, high, order}
        - noise_reduction: {enabled, method, noise_profile_duration}
        - normalize: {enabled, target_db}

    Returns
    -------
    processed : np.ndarray
        Processed audio

    Examples
    --------
    >>> config = {
    ...     "bandpass": {"low": 20, "high": 6000, "order": 4},
    ...     "noise_reduction": {"enabled": True, "method": "spectral_subtraction"},
    ...     "normalize": {"enabled": True, "target_db": -20}
    ... }
    >>> processed = preprocess_pipeline(audio, 48000, config)
    """
    processed = audio.copy()

    # Bandpass filter
    if "bandpass" in config:
        bp = config["bandpass"]
        processed = bandpass_filter(
            processed, sr, low=bp["low"], high=bp["high"], order=bp.get("order", 4)
        )

    # Noise reduction
    if config.get("noise_reduction", {}).get("enabled", False):
        nr = config["noise_reduction"]
        if nr.get("method") == "spectral_subtraction":
            processed = reduce_noise_spectral_subtraction(
                processed, sr, noise_profile_duration=nr.get("noise_profile_duration", 0.5)
            )

    # Normalization
    if config.get("normalize", {}).get("enabled", False):
        norm = config["normalize"]
        processed = normalize_audio(processed, target_db=norm.get("target_db", -20.0))

    logger.info("Preprocessing pipeline complete")
    return processed
