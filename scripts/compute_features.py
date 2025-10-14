#!/usr/bin/env python3
"""
compute_features.py

Compute acoustic features for detected thunder events.

Usage:
    python scripts/compute_features.py --audio audio.wav --events events.csv --output features.csv
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from thunder import io, features, utils


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compute acoustic features for thunder events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute features with default config
  python scripts/compute_features.py --audio audio.wav --events events.csv \\
      --output features.csv
  
  # Custom config file
  python scripts/compute_features.py --audio audio.wav --events events.csv \\
      --output features.csv --config configs/custom.yaml
        """,
    )

    parser.add_argument("--audio", required=True, help="Input audio file (WAV)")
    parser.add_argument("--events", required=True, help="Input events CSV")
    parser.add_argument("--output", required=True, help="Output features CSV")
    parser.add_argument(
        "--config", default="configs/default.yaml", help="Config YAML file"
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

    # Load audio
    logger.info(f"Loading audio: {args.audio}")
    audio, sr = io.load_audio(args.audio)
    logger.info(f"Audio: {len(audio)} samples @ {sr} Hz")

    # Load events
    logger.info(f"Loading events: {args.events}")
    events_df = pd.read_csv(args.events)
    events = events_df.to_dict("records")
    logger.info(f"Found {len(events)} events")

    if len(events) == 0:
        logger.error("No events found in CSV. Run detect_events.py first.")
        sys.exit(1)

    # Extract features
    logger.info("Extracting features...")
    features_config = config.get("features", {})
    feature_list = features.extract_all_features(audio, sr, events, features_config)

    logger.info(f"Extracted {len(feature_list)} feature sets")

    # Save to CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(feature_list)
    df.to_csv(output_path, index=False)
    logger.info(f"✓ Features saved: {output_path}")

    # Display summary statistics
    logger.info("\nFeature Summary:")
    numeric_cols = df.select_dtypes(include=["number"]).columns
    summary = df[numeric_cols].describe()
    logger.info(f"\n{summary}")

    logger.info("Feature extraction complete!")


if __name__ == "__main__":
    main()
