#!/usr/bin/env python3
"""
validate_config.py

Validate and display configuration settings.

Usage:
    python scripts/validate_config.py --config configs/default.yaml
"""

import argparse
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from thunder import utils


def convert_ms_to_samples(ms: float, sample_rate: int) -> int:
    """Convert milliseconds to sample count."""
    return int(ms * sample_rate / 1000)


def convert_ms_to_seconds(ms: float) -> float:
    """Convert milliseconds to seconds."""
    return ms / 1000.0


def validate_audio_config(config: dict) -> dict:
    """Validate audio configuration."""
    audio = config.get("audio", {})
    issues = []
    
    # Check sample rate
    sr = audio.get("sample_rate", 48000)
    if sr < 8000:
        issues.append(f"Sample rate too low: {sr} Hz (recommend >= 16000 Hz)")
    if sr > 96000:
        issues.append(f"Sample rate very high: {sr} Hz (may be unnecessary)")
    
    # Check frequency range
    highpass = audio.get("highpass_hz", 20)
    lowpass = audio.get("lowpass_hz", 6000)
    if highpass >= lowpass:
        issues.append(f"Invalid frequency range: {highpass}-{lowpass} Hz")
    if lowpass > sr / 2:
        issues.append(f"Lowpass {lowpass} Hz exceeds Nyquist limit {sr/2} Hz")
    
    return {"section": "audio", "issues": issues, "params": audio}


def validate_detect_config(config: dict) -> dict:
    """Validate detection configuration."""
    detect = config.get("detect", {})
    issues = []
    
    # Check frame lengths
    frame_len = detect.get("frame_len_ms", 20)
    hop_len = detect.get("hop_len_ms", 10)
    
    if hop_len > frame_len:
        issues.append(f"Hop length {hop_len}ms > frame length {frame_len}ms")
    
    overlap = (frame_len - hop_len) / frame_len * 100
    if overlap < 25:
        issues.append(f"Low overlap: {overlap:.1f}% (recommend >= 50%)")
    
    # Check thresholds
    energy_db = detect.get("energy_thresh_db", -25)
    if energy_db > -10:
        issues.append(f"Energy threshold very high: {energy_db} dB (may miss events)")
    if energy_db < -50:
        issues.append(f"Energy threshold very low: {energy_db} dB (may detect noise)")
    
    # Check merge gap vs min event
    merge_gap = detect.get("merge_gap_ms", 300)
    min_event = detect.get("min_event_ms", 150)
    if min_event > merge_gap:
        issues.append(f"Min event {min_event}ms > merge gap {merge_gap}ms")
    
    return {"section": "detect", "issues": issues, "params": detect}


def validate_features_config(config: dict) -> dict:
    """Validate features configuration."""
    features = config.get("features", {})
    audio = config.get("audio", {})
    sr = audio.get("sample_rate", 48000)
    
    issues = []
    
    # Check STFT parameters
    stft_win_ms = features.get("stft_win_ms", 64)
    stft_hop_ms = features.get("stft_hop_ms", 16)
    
    stft_win_samples = convert_ms_to_samples(stft_win_ms, sr)
    stft_hop_samples = convert_ms_to_samples(stft_hop_ms, sr)
    
    # Find nearest power of 2 for n_fft
    n_fft_recommended = 2 ** (stft_win_samples.bit_length())
    
    time_freq = features.get("time_frequency", {})
    stft = time_freq.get("stft", {})
    n_fft_actual = stft.get("n_fft", 2048)
    
    if n_fft_actual < stft_win_samples:
        issues.append(f"n_fft {n_fft_actual} < window samples {stft_win_samples}")
    
    if abs(n_fft_actual - n_fft_recommended) > 512:
        issues.append(
            f"n_fft {n_fft_actual} differs from recommended {n_fft_recommended}"
        )
    
    # Check mel bands
    n_mels = features.get("n_mels", 64)
    if n_mels < 20:
        issues.append(f"Too few mel bands: {n_mels} (recommend >= 40)")
    if n_mels > 128:
        issues.append(f"Very many mel bands: {n_mels} (may be slow)")
    
    return {"section": "features", "issues": issues, "params": features}


def validate_distance_config(config: dict) -> dict:
    """Validate distance estimation configuration."""
    distance = config.get("distance", {})
    issues = []
    
    # Check speed of sound
    c = distance.get("speed_of_sound", 343.5)
    if c < 330 or c > 350:
        issues.append(f"Speed of sound {c} m/s outside typical range (330-350 m/s)")
    
    # Check temperature
    temp = distance.get("reference_temp", 20)
    if temp < -40 or temp > 50:
        issues.append(f"Reference temperature {temp}°C outside typical range")
    
    # Verify formula
    c_expected = 331.5 + 0.6 * temp
    if abs(c - c_expected) > 1.0:
        issues.append(
            f"Speed of sound {c} m/s inconsistent with temp {temp}°C "
            f"(expected {c_expected:.1f} m/s)"
        )
    
    return {"section": "distance", "issues": issues, "params": distance}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate thunder acoustics configuration"
    )
    parser.add_argument(
        "--config",
        default="configs/default.yaml",
        help="Configuration YAML file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    
    args = parser.parse_args()
    
    # Load config
    print(f"Loading configuration: {args.config}\n")
    config = utils.load_config(args.config)
    
    # Validate all sections
    results = [
        validate_audio_config(config),
        validate_detect_config(config),
        validate_features_config(config),
        validate_distance_config(config),
    ]
    
    # Calculate summary
    total_issues = sum(len(r["issues"]) for r in results)
    
    if args.json:
        print(json.dumps({"results": results, "total_issues": total_issues}, indent=2))
    else:
        # Human-readable output
        print("=" * 60)
        print("Configuration Validation Report")
        print("=" * 60)
        print()
        
        for result in results:
            section = result["section"]
            issues = result["issues"]
            params = result["params"]
            
            print(f"[{section.upper()}]")
            print(f"  Parameters: {len(params)} entries")
            
            if issues:
                print(f"  ⚠ Issues found: {len(issues)}")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print("  ✓ No issues")
            print()
        
        print("=" * 60)
        if total_issues == 0:
            print("✓ Configuration is valid!")
        else:
            print(f"⚠ Found {total_issues} issue(s)")
        print("=" * 60)
        
        # Print computed values
        audio = config.get("audio", {})
        detect = config.get("detect", {})
        features = config.get("features", {})
        
        sr = audio.get("sample_rate", 48000)
        
        print()
        print("Computed Values:")
        print(f"  Sample rate: {sr} Hz")
        print(f"  Nyquist frequency: {sr/2} Hz")
        print()
        
        frame_len_ms = detect.get("frame_len_ms", 20)
        hop_len_ms = detect.get("hop_len_ms", 10)
        print(f"  Detection frame: {frame_len_ms}ms = {convert_ms_to_samples(frame_len_ms, sr)} samples")
        print(f"  Detection hop: {hop_len_ms}ms = {convert_ms_to_samples(hop_len_ms, sr)} samples")
        print(f"  Frame overlap: {(frame_len_ms - hop_len_ms) / frame_len_ms * 100:.1f}%")
        print()
        
        stft_win_ms = features.get("stft_win_ms", 64)
        stft_hop_ms = features.get("stft_hop_ms", 16)
        print(f"  STFT window: {stft_win_ms}ms = {convert_ms_to_samples(stft_win_ms, sr)} samples")
        print(f"  STFT hop: {stft_hop_ms}ms = {convert_ms_to_samples(stft_hop_ms, sr)} samples")
        print(f"  STFT overlap: {(stft_win_ms - stft_hop_ms) / stft_win_ms * 100:.1f}%")
    
    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()
