#!/usr/bin/env python3
"""
detect_events.py

Detect thunder events in audio files.

Usage:
    python scripts/detect_events.py --audio path/to/audio.wav --output events.csv
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from thunder import io, preprocess, detection, utils, metadata


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Detect thunder events in audio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect events with default config
  python scripts/detect_events.py --audio audio.wav --output events.csv
  
  # Custom config file
  python scripts/detect_events.py --audio audio.wav --output events.csv \\
      --config configs/custom.yaml
  
  # Custom thresholds
  python scripts/detect_events.py --audio audio.wav --output events.csv \\
      --energy-threshold 0.02 --merge-gap 1.0
        """,
    )

    parser.add_argument("--audio", required=True, help="Input audio file (WAV)")
    parser.add_argument("--output", required=True, help="Output CSV file")
    parser.add_argument(
        "--config", default="configs/default.yaml", help="Config YAML file"
    )
    parser.add_argument(
        "--energy-threshold",
        type=float,
        help="Energy threshold (overrides config)",
    )
    parser.add_argument(
        "--spectral-threshold",
        type=float,
        help="Spectral threshold (overrides config)",
    )
    parser.add_argument(
        "--merge-gap",
        type=float,
        help="Event merge gap in seconds (overrides config)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    utils.setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)

    # Load config
    logger.info(f"Loading config: {args.config}")
    config = utils.load_config(args.config)

    # Override config with CLI args
    detection_config = config.get("detection", {})
    if args.energy_threshold is not None:
        detection_config["energy_threshold"] = args.energy_threshold
    if args.spectral_threshold is not None:
        detection_config["spectral_threshold"] = args.spectral_threshold
    if args.merge_gap is not None:
        detection_config["merge_gap"] = args.merge_gap

    # Load audio
    logger.info(f"Loading audio: {args.audio}")
    audio, sr = io.load_audio(args.audio)
    logger.info(f"Audio: {len(audio)} samples @ {sr} Hz ({len(audio) / sr:.2f}s)")

    # Validate audio
    io.validate_audio(audio, sr)

    # Preprocessing
    preprocess_config = config.get("preprocessing", {})
    logger.info("Preprocessing audio...")
    audio_processed = preprocess.preprocess_pipeline(audio, sr, preprocess_config)

    # Event detection
    logger.info("Detecting thunder events...")
    events = detection.detect_thunder_events(audio_processed, sr, detection_config)

    logger.info(f"Detected {len(events)} events")

    if len(events) == 0:
        logger.warning("No events detected. Adjust thresholds if needed.")
    else:
        # Display summary
        for i, event in enumerate(events):
            logger.info(
                f"  Event {i + 1}: "
                f"{event['start']:.2f}s - {event['end']:.2f}s "
                f"(duration: {event['duration']:.2f}s, "
                f"peak: {event['peak_amplitude']:.4f})"
            )

    # Save to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(events)
    df.to_csv(output_path, index=False)
    logger.info(f"✓ Events saved: {output_path}")

    # Save metadata
    meta_path = output_path.parent / "meta.json"
    meta = metadata.create_metadata(
        source_url=args.audio,
        config=config,
        additional_info={
            "num_events": len(events),
            "audio_duration": len(audio) / sr,
        },
    )
    metadata.save_metadata(meta, meta_path)

    logger.info("Detection complete!")


if __name__ == "__main__":
    main()
