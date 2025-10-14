#!/usr/bin/env python3
"""
migrate_config.py

Migrate old configuration format to new format with audio/detect/features sections.

Usage:
    python scripts/migrate_config.py --input configs/old.yaml --output configs/new.yaml
"""

import argparse
import sys
from pathlib import Path
import yaml


def ms_to_seconds(ms: float) -> float:
    """Convert milliseconds to seconds."""
    return ms / 1000.0


def seconds_to_ms(seconds: float) -> float:
    """Convert seconds to milliseconds."""
    return seconds * 1000.0


def migrate_config(old_config: dict) -> dict:
    """
    Migrate configuration from old to new format.
    
    Old format uses 'preprocessing', 'detection', 'features' (in seconds).
    New format adds 'audio', 'detect', 'viz' (in milliseconds where appropriate).
    """
    new_config = {}
    
    # Header
    new_config["# Configuration"] = "Thunder Acoustics in the Wild - v1.0"
    
    # Extract preprocessing (old format)
    preprocess = old_config.get("preprocessing", {})
    bandpass = preprocess.get("bandpass", {})
    normalize = preprocess.get("normalize", {})
    
    # Build audio section (new format)
    new_config["audio"] = {
        "sample_rate": preprocess.get("sample_rate", 48000),
        "bit_depth": preprocess.get("bit_depth", 24),
        "channels": preprocess.get("channels", 1),
        "highpass_hz": bandpass.get("low_cutoff", bandpass.get("low", 20)),
        "lowpass_hz": bandpass.get("high_cutoff", bandpass.get("high", 6000)),
        "normalize": normalize.get("enabled", True),
    }
    
    # Keep preprocessing section for backward compatibility
    new_config["preprocessing"] = preprocess
    
    # Extract detection (old format)
    detection_old = old_config.get("detection", {})
    
    # Build detect section (new format with milliseconds)
    window_size_sec = detection_old.get("window_size", 0.02)
    hop_length_sec = detection_old.get("hop_length", 0.01)
    merge_gap_sec = detection_old.get("merge_gap", 0.3)
    min_duration_sec = detection_old.get("min_duration", 0.15)
    
    new_config["detect"] = {
        "frame_len_ms": int(seconds_to_ms(window_size_sec)),
        "hop_len_ms": int(seconds_to_ms(hop_length_sec)),
        "energy_thresh_db": -25,  # Default value (not in old format)
        "merge_gap_ms": int(seconds_to_ms(merge_gap_sec)),
        "min_event_ms": int(seconds_to_ms(min_duration_sec)),
        "spectral_change_thresh": detection_old.get("spectral_threshold", 0.1),
    }
    
    # Keep detection section for backward compatibility
    new_config["detection"] = detection_old
    
    # Extract features (old format)
    features_old = old_config.get("features", {})
    time_freq = features_old.get("time_frequency", {})
    stft = time_freq.get("stft", {})
    mfcc = time_freq.get("mfcc", {})
    cwt = time_freq.get("cwt", {})
    
    # Calculate STFT timing from sample count
    sample_rate = new_config["audio"]["sample_rate"]
    n_fft = stft.get("n_fft", 2048)
    hop_length = stft.get("hop_length", 512)
    
    stft_win_ms = int(n_fft / sample_rate * 1000)
    stft_hop_ms = int(hop_length / sample_rate * 1000)
    
    # Build features section (new format)
    new_config["features"] = {
        "stft_win_ms": stft_win_ms,
        "stft_hop_ms": stft_hop_ms,
        "n_mels": mfcc.get("n_mels", 64),
        "mfcc_n": mfcc.get("n_mfcc", 13),
        "cwt_wavelet": cwt.get("wavelet", "morlet"),
    }
    
    # Merge with full old features structure
    new_config["features"].update(features_old)
    
    # Build viz section (new format)
    visualization = old_config.get("visualization", {})
    spectrogram = visualization.get("spectrogram", {})
    
    new_config["viz"] = {
        "spectrogram_db_range": spectrogram.get("vmax", 0) - spectrogram.get("vmin", -80),
        "dpi": visualization.get("dpi", 160),
    }
    
    # Keep visualization section for backward compatibility
    new_config["visualization"] = visualization
    
    # Extract distance (old format)
    distance_old = old_config.get("distance", {})
    
    # Build distance section (enhanced)
    new_config["distance"] = {
        "enable_flash_alignment": True,  # New feature
        "speed_of_sound": distance_old.get("speed_of_sound", 343.5),
        "reference_temp": distance_old.get("reference_temp", 20),
    }
    
    # Merge with old distance structure
    new_config["distance"].update(distance_old)
    
    # Copy other sections as-is
    for key in old_config:
        if key not in ["preprocessing", "detection", "features", "visualization", "distance"]:
            new_config[key] = old_config[key]
    
    return new_config


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate thunder acoustics configuration to new format"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input configuration YAML file (old format)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output configuration YAML file (new format)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output without saving",
    )
    
    args = parser.parse_args()
    
    # Load old config
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading old configuration: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        old_config = yaml.safe_load(f)
    
    # Migrate
    print("Migrating configuration...")
    new_config = migrate_config(old_config)
    
    # Output
    output_yaml = yaml.dump(
        new_config,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    
    if args.dry_run:
        print("\n" + "=" * 60)
        print("Migrated Configuration (dry run)")
        print("=" * 60)
        print(output_yaml)
    else:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_yaml)
        
        print(f"✓ Migrated configuration saved: {output_path}")
        print()
        print("Validation recommended:")
        print(f"  python scripts/validate_config.py --config {output_path}")


if __name__ == "__main__":
    main()
