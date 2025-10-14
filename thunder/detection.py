"""
thunder.detection
=================

Thunder event detection using energy and spectral analysis.
"""

import numpy as np
from scipy import signal
import librosa
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def compute_energy_envelope(
    audio: np.ndarray, sr: int, window_size: float = 0.05, hop_length: float = 0.01
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute energy envelope of audio.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    window_size : float, default=0.05
        Window size in seconds
    hop_length : float, default=0.01
        Hop length in seconds

    Returns
    -------
    times : np.ndarray
        Time stamps for each frame
    energy : np.ndarray
        Energy envelope

    Examples
    --------
    >>> times, energy = compute_energy_envelope(audio, 48000)
    """
    window_samples = int(window_size * sr)
    hop_samples = int(hop_length * sr)

    # RMS energy per frame
    energy = librosa.feature.rms(
        y=audio, frame_length=window_samples, hop_length=hop_samples
    )[0]

    times = librosa.frames_to_time(
        np.arange(len(energy)), sr=sr, hop_length=hop_samples
    )

    return times, energy


def compute_spectral_flux(
    audio: np.ndarray,
    sr: int,
    n_fft: int = 2048,
    hop_length: int = 512,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute spectral flux (rate of spectral change).

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    n_fft : int, default=2048
        FFT window size
    hop_length : int, default=512
        Hop length

    Returns
    -------
    times : np.ndarray
        Time stamps
    flux : np.ndarray
        Spectral flux values

    Examples
    --------
    >>> times, flux = compute_spectral_flux(audio, 48000)
    """
    stft = np.abs(librosa.stft(audio, n_fft=n_fft, hop_length=hop_length))

    # Compute differences between consecutive frames
    flux = np.sqrt(np.sum(np.diff(stft, axis=1) ** 2, axis=0))

    times = librosa.frames_to_time(np.arange(len(flux)), sr=sr, hop_length=hop_length)

    return times, flux


def detect_events_energy(
    audio: np.ndarray,
    sr: int,
    energy_threshold: float = 0.01,
    window_size: float = 0.05,
    hop_length: float = 0.01,
) -> List[Tuple[float, float]]:
    """
    Detect events using energy threshold.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    energy_threshold : float, default=0.01
        Relative energy threshold (0-1)
    window_size : float, default=0.05
        Window size in seconds
    hop_length : float, default=0.01
        Hop length in seconds

    Returns
    -------
    events : list of (start, end) tuples
        Event boundaries in seconds

    Examples
    --------
    >>> events = detect_events_energy(audio, 48000, energy_threshold=0.01)
    """
    times, energy = compute_energy_envelope(audio, sr, window_size, hop_length)

    # Threshold
    threshold = energy_threshold * np.max(energy)
    above_threshold = energy > threshold

    # Find contiguous regions
    events = []
    in_event = False
    start_time = None

    for i, (time, above) in enumerate(zip(times, above_threshold)):
        if above and not in_event:
            # Event start
            start_time = time
            in_event = True
        elif not above and in_event:
            # Event end
            events.append((start_time, time))
            in_event = False

    # Close final event if needed
    if in_event:
        events.append((start_time, times[-1]))

    logger.info(f"Detected {len(events)} events (energy threshold)")
    return events


def detect_events_spectral(
    audio: np.ndarray,
    sr: int,
    spectral_threshold: float = 0.1,
    n_fft: int = 2048,
    hop_length: int = 512,
) -> List[Tuple[float, float]]:
    """
    Detect events using spectral flux.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    spectral_threshold : float, default=0.1
        Spectral flux threshold (relative to max)
    n_fft : int, default=2048
        FFT window size
    hop_length : int, default=512
        Hop length

    Returns
    -------
    events : list of (start, end) tuples
        Event boundaries in seconds

    Examples
    --------
    >>> events = detect_events_spectral(audio, 48000)
    """
    times, flux = compute_spectral_flux(audio, sr, n_fft, hop_length)

    # Threshold
    threshold = spectral_threshold * np.max(flux)
    above_threshold = flux > threshold

    # Find peaks
    peaks, _ = signal.find_peaks(flux, height=threshold)

    # Convert to time
    events = []
    for peak in peaks:
        if peak < len(times):
            peak_time = times[peak]
            # Simple event: ±0.5s around peak
            start = max(0, peak_time - 0.5)
            end = min(times[-1], peak_time + 0.5)
            events.append((start, end))

    logger.info(f"Detected {len(events)} events (spectral flux)")
    return events


def merge_events(
    events: List[Tuple[float, float]], merge_gap: float = 0.5, min_duration: float = 0.1
) -> List[Tuple[float, float]]:
    """
    Merge close events and filter by duration.

    Parameters
    ----------
    events : list of (start, end) tuples
        Input events
    merge_gap : float, default=0.5
        Merge events closer than this (seconds)
    min_duration : float, default=0.1
        Minimum event duration (seconds)

    Returns
    -------
    merged : list of (start, end) tuples
        Merged and filtered events

    Examples
    --------
    >>> merged = merge_events(events, merge_gap=0.5, min_duration=0.1)
    """
    if not events:
        return []

    # Sort by start time
    events = sorted(events, key=lambda x: x[0])

    merged = []
    current_start, current_end = events[0]

    for start, end in events[1:]:
        if start - current_end <= merge_gap:
            # Merge with current event
            current_end = max(current_end, end)
        else:
            # Save current and start new
            if current_end - current_start >= min_duration:
                merged.append((current_start, current_end))
            current_start, current_end = start, end

    # Add final event
    if current_end - current_start >= min_duration:
        merged.append((current_start, current_end))

    logger.info(f"Merged {len(events)} → {len(merged)} events")
    return merged


def detect_thunder_events(
    audio: np.ndarray,
    sr: int,
    config: dict,
) -> List[dict]:
    """
    Detect thunder events using combined energy + spectral analysis.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    config : dict
        Detection configuration with keys:
        - energy_threshold
        - spectral_threshold
        - window_size
        - hop_length
        - merge_gap
        - min_duration

    Returns
    -------
    events : list of dict
        Each dict contains: start, end, duration, peak_time, peak_amplitude

    Examples
    --------
    >>> config = {"energy_threshold": 0.01, "merge_gap": 0.5}
    >>> events = detect_thunder_events(audio, 48000, config)
    """
    # Energy-based detection
    events_energy = detect_events_energy(
        audio,
        sr,
        energy_threshold=config.get("energy_threshold", 0.01),
        window_size=config.get("window_size", 0.05),
        hop_length=config.get("hop_length", 0.01),
    )

    # Spectral-based detection
    events_spectral = detect_events_spectral(
        audio,
        sr,
        spectral_threshold=config.get("spectral_threshold", 0.1),
    )

    # Combine (union)
    all_events = events_energy + events_spectral

    # Merge close events
    merged_events = merge_events(
        all_events,
        merge_gap=config.get("merge_gap", 0.5),
        min_duration=config.get("min_duration", 0.1),
    )

    # Extract peak info for each event
    detailed_events = []
    for start, end in merged_events:
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        segment = audio[start_sample:end_sample]

        if len(segment) > 0:
            peak_idx = np.argmax(np.abs(segment))
            peak_time = start + peak_idx / sr
            peak_amplitude = segment[peak_idx]

            detailed_events.append(
                {
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "peak_time": peak_time,
                    "peak_amplitude": float(peak_amplitude),
                }
            )

    logger.info(f"Final detection: {len(detailed_events)} thunder events")
    return detailed_events
