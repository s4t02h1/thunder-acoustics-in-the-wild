"""
thunder.features
================

Acoustic feature extraction for thunder events.

Features:
- Time domain: peak, RMS, crest, zero-crossing, attack/decay
- Frequency domain: spectral centroid, bandwidth, rolloff, slope
- Time-frequency: STFT, CWT, MFCC
- Statistical: kurtosis, skewness, energy bands
"""

import numpy as np
from scipy import signal, stats
import librosa
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


# ========================================
# Time Domain Features
# ========================================


def compute_peak_amplitude(audio: np.ndarray) -> float:
    """Peak amplitude."""
    return float(np.abs(audio).max())


def compute_rms(audio: np.ndarray) -> float:
    """Root Mean Square energy."""
    return float(np.sqrt(np.mean(audio**2)))


def compute_crest_factor(audio: np.ndarray) -> float:
    """Crest factor = peak / RMS."""
    rms = compute_rms(audio)
    if rms == 0:
        return 0.0
    return float(compute_peak_amplitude(audio) / rms)


def compute_zero_crossing_rate(audio: np.ndarray, sr: int) -> float:
    """Zero crossing rate (crossings per second)."""
    zcr = librosa.feature.zero_crossing_rate(audio)[0]
    return float(np.mean(zcr) * sr)


def compute_attack_decay_time(
    audio: np.ndarray, sr: int, threshold: float = 0.1
) -> Tuple[float, float]:
    """
    Attack time: 10% → peak
    Decay time: peak → 10%
    """
    envelope = np.abs(audio)
    peak_idx = np.argmax(envelope)
    peak_val = envelope[peak_idx]
    threshold_val = threshold * peak_val

    # Attack: find first sample above threshold before peak
    attack_samples = envelope[:peak_idx]
    attack_idx = np.where(attack_samples > threshold_val)[0]
    attack_time = attack_idx[0] / sr if len(attack_idx) > 0 else 0.0

    # Decay: find first sample below threshold after peak
    decay_samples = envelope[peak_idx:]
    decay_idx = np.where(decay_samples < threshold_val)[0]
    decay_time = decay_idx[0] / sr if len(decay_idx) > 0 else 0.0

    return float(attack_time), float(decay_time)


def extract_time_domain_features(audio: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract all time domain features."""
    attack, decay = compute_attack_decay_time(audio, sr)

    return {
        "peak_amplitude": compute_peak_amplitude(audio),
        "rms": compute_rms(audio),
        "crest_factor": compute_crest_factor(audio),
        "zero_crossing_rate": compute_zero_crossing_rate(audio, sr),
        "attack_time": attack,
        "decay_time": decay,
    }


# ========================================
# Frequency Domain Features
# ========================================


def compute_spectral_centroid(audio: np.ndarray, sr: int) -> float:
    """Spectral centroid (center of mass of spectrum)."""
    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    return float(np.mean(centroid))


def compute_spectral_bandwidth(audio: np.ndarray, sr: int) -> float:
    """Spectral bandwidth (spread around centroid)."""
    bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
    return float(np.mean(bandwidth))


def compute_spectral_rolloff(audio: np.ndarray, sr: int, rolloff_percent: float = 0.85) -> float:
    """Spectral rolloff (frequency below which X% of energy is contained)."""
    rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr, roll_percent=rolloff_percent)[0]
    return float(np.mean(rolloff))


def compute_spectral_slope(audio: np.ndarray, sr: int, n_fft: int = 2048) -> float:
    """
    Spectral slope (linear regression of log-magnitude spectrum).
    Negative slope indicates more low-frequency energy (typical of thunder).
    """
    spectrum = np.abs(librosa.stft(audio, n_fft=n_fft))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    log_spectrum = np.log(spectrum + 1e-10)
    mean_log_spectrum = np.mean(log_spectrum, axis=1)

    # Linear regression
    slope, intercept = np.polyfit(freqs, mean_log_spectrum, 1)
    return float(slope)


def compute_dominant_frequency(audio: np.ndarray, sr: int, n_fft: int = 2048) -> float:
    """Dominant frequency (frequency with highest energy)."""
    spectrum = np.abs(librosa.stft(audio, n_fft=n_fft))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    mean_spectrum = np.mean(spectrum, axis=1)
    dominant_idx = np.argmax(mean_spectrum)
    return float(freqs[dominant_idx])


def extract_frequency_domain_features(audio: np.ndarray, sr: int) -> Dict[str, float]:
    """Extract all frequency domain features."""
    return {
        "spectral_centroid": compute_spectral_centroid(audio, sr),
        "spectral_bandwidth": compute_spectral_bandwidth(audio, sr),
        "spectral_rolloff": compute_spectral_rolloff(audio, sr),
        "spectral_slope": compute_spectral_slope(audio, sr),
        "dominant_frequency": compute_dominant_frequency(audio, sr),
    }


# ========================================
# Time-Frequency Features
# ========================================


def extract_mfcc(audio: np.ndarray, sr: int, n_mfcc: int = 13) -> np.ndarray:
    """Extract MFCC (Mel-Frequency Cepstral Coefficients)."""
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
    return mfcc


def extract_stft_features(
    audio: np.ndarray, sr: int, n_fft: int = 2048, hop_length: int = 512
) -> Dict[str, np.ndarray]:
    """Extract STFT representation."""
    stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
    magnitude = np.abs(stft)
    phase = np.angle(stft)

    return {
        "stft_magnitude": magnitude,
        "stft_phase": phase,
        "freqs": librosa.fft_frequencies(sr=sr, n_fft=n_fft),
        "times": librosa.frames_to_time(np.arange(magnitude.shape[1]), sr=sr, hop_length=hop_length),
    }


def extract_time_frequency_features(audio: np.ndarray, sr: int, config: dict) -> Dict:
    """Extract time-frequency features."""
    n_mfcc = config.get("mfcc_coeffs", 13)
    n_fft = config.get("stft_window", 2048)
    hop_length = config.get("hop_length", 512)

    mfcc = extract_mfcc(audio, sr, n_mfcc)
    stft_data = extract_stft_features(audio, sr, n_fft, hop_length)

    return {
        "mfcc": mfcc,
        "mfcc_mean": np.mean(mfcc, axis=1),
        "mfcc_std": np.std(mfcc, axis=1),
        "stft": stft_data,
    }


# ========================================
# Statistical Features
# ========================================


def compute_kurtosis(audio: np.ndarray) -> float:
    """Kurtosis (tailedness of distribution)."""
    return float(stats.kurtosis(audio))


def compute_skewness(audio: np.ndarray) -> float:
    """Skewness (asymmetry of distribution)."""
    return float(stats.skew(audio))


def compute_energy_bands(
    audio: np.ndarray, sr: int, bands: List[Tuple[float, float]]
) -> Dict[str, float]:
    """
    Compute energy in frequency bands.

    Parameters
    ----------
    audio : np.ndarray
        Input audio
    sr : int
        Sample rate
    bands : list of (low, high) tuples
        Frequency bands in Hz

    Returns
    -------
    energy_dict : dict
        Energy per band

    Examples
    --------
    >>> bands = [(20, 100), (100, 500), (500, 6000)]
    >>> energy = compute_energy_bands(audio, 48000, bands)
    """
    spectrum = np.abs(librosa.stft(audio))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=spectrum.shape[0] * 2 - 2)

    energy_dict = {}
    for low, high in bands:
        mask = (freqs >= low) & (freqs <= high)
        band_energy = np.sum(spectrum[mask, :] ** 2)
        energy_dict[f"energy_{low}_{high}Hz"] = float(band_energy)

    return energy_dict


def extract_statistical_features(
    audio: np.ndarray, sr: int, energy_bands: List[Tuple[float, float]]
) -> Dict[str, float]:
    """Extract statistical features."""
    features = {
        "kurtosis": compute_kurtosis(audio),
        "skewness": compute_skewness(audio),
    }

    # Energy bands
    band_energy = compute_energy_bands(audio, sr, energy_bands)
    features.update(band_energy)

    return features


# ========================================
# Main Feature Extraction
# ========================================


def extract_event_features(
    audio: np.ndarray, sr: int, event: dict, config: dict
) -> Dict:
    """
    Extract all features for a single event.

    Parameters
    ----------
    audio : np.ndarray
        Full audio array
    sr : int
        Sample rate
    event : dict
        Event dict with 'start' and 'end' keys
    config : dict
        Feature configuration

    Returns
    -------
    features : dict
        All extracted features

    Examples
    --------
    >>> features = extract_event_features(audio, 48000, event, config)
    """
    # Extract event segment
    start_sample = int(event["start"] * sr)
    end_sample = int(event["end"] * sr)
    segment = audio[start_sample:end_sample]

    if len(segment) == 0:
        logger.warning(f"Empty event segment: {event}")
        return {}

    # Time domain
    time_features = extract_time_domain_features(segment, sr)

    # Frequency domain
    freq_features = extract_frequency_domain_features(segment, sr)

    # Time-frequency
    tf_features = extract_time_frequency_features(segment, sr, config)

    # Statistical
    energy_bands = config.get("energy_bands", [[20, 100], [100, 500], [500, 6000]])
    stat_features = extract_statistical_features(segment, sr, energy_bands)

    # Combine
    features = {
        **event,
        **time_features,
        **freq_features,
        **stat_features,
        "mfcc_mean": tf_features["mfcc_mean"].tolist(),
        "mfcc_std": tf_features["mfcc_std"].tolist(),
    }

    return features


def extract_all_features(
    audio: np.ndarray, sr: int, events: List[dict], config: dict
) -> List[Dict]:
    """
    Extract features for all events.

    Parameters
    ----------
    audio : np.ndarray
        Full audio array
    sr : int
        Sample rate
    events : list of dict
        Detected events
    config : dict
        Feature configuration

    Returns
    -------
    all_features : list of dict
        Features for all events

    Examples
    --------
    >>> features = extract_all_features(audio, 48000, events, config)
    """
    all_features = []

    for i, event in enumerate(events):
        logger.info(f"Extracting features for event {i + 1}/{len(events)}")
        features = extract_event_features(audio, sr, event, config)
        features["event_id"] = i
        all_features.append(features)

    logger.info(f"Extracted features for {len(all_features)} events")
    return all_features
