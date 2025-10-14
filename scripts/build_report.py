#!/usr/bin/env python3
"""
build_report.py

Generate a Markdown report from analysis results.

Usage:
    python scripts/build_report.py --events events.csv --features features.csv \\
        --meta meta.json --output report.md
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import json
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from thunder import utils


def generate_report(
    events_df: pd.DataFrame,
    features_df: pd.DataFrame | None,
    metadata: dict,
    output_path: str | Path,
    viz_dir: Path | None = None,
):
    """
    Generate Markdown report.

    Parameters
    ----------
    events_df : DataFrame
        Events dataframe
    features_df : DataFrame or None
        Features dataframe (optional)
    metadata : dict
        Analysis metadata
    output_path : str or Path
        Output Markdown file
    viz_dir : Path or None
        Directory containing visualizations
    """
    output_path = Path(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        # Header
        f.write("# Thunder Acoustic Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Metadata section
        f.write("## Metadata\n\n")
        f.write(f"- **Source:** {metadata.get('source_url', 'N/A')}\n")
        f.write(f"- **Video ID:** {metadata.get('video_id', 'N/A')}\n")
        f.write(f"- **Analysis Date:** {metadata.get('analysis_timestamp', 'N/A')}\n")
        f.write(f"- **Version:** {metadata.get('version', 'N/A')}\n")
        f.write(f"- **Config Hash:** `{metadata.get('config_hash', 'N/A')}`\n\n")

        # Ethics notice
        if metadata.get("citation_required"):
            f.write("### Ethics Notice\n\n")
            f.write("⚠️ **Citation Required:** Please cite the original video creator.\n")
            f.write(
                "- Respect copyright and terms of service\n"
                "- Use for research purposes only\n"
                "- No surveillance or privacy invasion\n\n"
            )

        # Event summary
        f.write("## Event Detection Summary\n\n")
        f.write(f"**Total Events Detected:** {len(events_df)}\n\n")

        if len(events_df) > 0:
            f.write("### Event Statistics\n\n")
            f.write(f"- **Mean Duration:** {events_df['duration'].mean():.3f} seconds\n")
            f.write(f"- **Std Duration:** {events_df['duration'].std():.3f} seconds\n")
            f.write(f"- **Min Duration:** {events_df['duration'].min():.3f} seconds\n")
            f.write(f"- **Max Duration:** {events_df['duration'].max():.3f} seconds\n\n")

            if "peak_amplitude" in events_df.columns:
                f.write(
                    f"- **Mean Peak Amplitude:** {events_df['peak_amplitude'].mean():.4f}\n"
                )
                f.write(
                    f"- **Max Peak Amplitude:** {events_df['peak_amplitude'].max():.4f}\n\n"
                )

            # Event table
            f.write("### Detected Events\n\n")
            f.write("| Event | Start (s) | End (s) | Duration (s) | Peak Amplitude |\n")
            f.write("|-------|-----------|---------|--------------|----------------|\n")
            for idx, row in events_df.iterrows():
                f.write(
                    f"| {idx + 1} | {row['start']:.2f} | {row['end']:.2f} | "
                    f"{row['duration']:.2f} | {row.get('peak_amplitude', 0):.4f} |\n"
                )
            f.write("\n")

        # Feature summary
        if features_df is not None and len(features_df) > 0:
            f.write("## Feature Extraction Summary\n\n")

            numeric_cols = features_df.select_dtypes(include=["number"]).columns
            exclude = ["event_id", "start", "end", "duration"]
            feature_cols = [c for c in numeric_cols if c not in exclude]

            f.write(f"**Total Features Extracted:** {len(feature_cols)}\n\n")

            f.write("### Feature Statistics\n\n")
            summary = features_df[feature_cols].describe()

            f.write("| Feature | Mean | Std | Min | Max |\n")
            f.write("|---------|------|-----|-----|-----|\n")
            for col in feature_cols[:10]:  # Top 10 features
                if col in summary.columns:
                    mean = summary.loc["mean", col]
                    std = summary.loc["std", col]
                    min_val = summary.loc["min", col]
                    max_val = summary.loc["max", col]
                    f.write(
                        f"| {col} | {mean:.3e} | {std:.3e} | {min_val:.3e} | {max_val:.3e} |\n"
                    )
            f.write("\n")

        # Visualizations
        if viz_dir and viz_dir.exists():
            f.write("## Visualizations\n\n")

            waveform = viz_dir / "waveform.png"
            if waveform.exists():
                rel_path = waveform.relative_to(output_path.parent)
                f.write("### Waveform with Events\n\n")
                f.write(f"![Waveform]({rel_path})\n\n")

            spectrogram = viz_dir / "spectrogram.png"
            if spectrogram.exists():
                rel_path = spectrogram.relative_to(output_path.parent)
                f.write("### Spectrogram\n\n")
                f.write(f"![Spectrogram]({rel_path})\n\n")

            histograms = viz_dir / "feature_histograms.png"
            if histograms.exists():
                rel_path = histograms.relative_to(output_path.parent)
                f.write("### Feature Distributions\n\n")
                f.write(f"![Feature Histograms]({rel_path})\n\n")

        # Configuration
        f.write("## Analysis Configuration\n\n")
        f.write("```yaml\n")
        config = metadata.get("config", {})
        import yaml

        f.write(yaml.dump(config, default_flow_style=False, allow_unicode=True))
        f.write("```\n\n")

        # Footer
        f.write("---\n\n")
        f.write("*Report generated by Thunder Acoustics in the Wild v0.1.0*\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Markdown report from analysis results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report with all components
  python scripts/build_report.py --events events.csv --features features.csv \\
      --meta meta.json --viz-dir outputs/viz/ --output report.md
  
  # Minimal report (events only)
  python scripts/build_report.py --events events.csv --meta meta.json \\
      --output report.md
        """,
    )

    parser.add_argument("--events", required=True, help="Input events CSV")
    parser.add_argument("--features", help="Input features CSV (optional)")
    parser.add_argument("--meta", required=True, help="Input metadata JSON")
    parser.add_argument("--viz-dir", help="Visualization directory (optional)")
    parser.add_argument("--output", required=True, help="Output Markdown report")
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

    # Load events
    logger.info(f"Loading events: {args.events}")
    events_df = pd.read_csv(args.events)
    logger.info(f"Found {len(events_df)} events")

    # Load features (optional)
    features_df = None
    if args.features:
        logger.info(f"Loading features: {args.features}")
        features_df = pd.read_csv(args.features)

    # Load metadata
    logger.info(f"Loading metadata: {args.meta}")
    with open(args.meta, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Visualization directory
    viz_dir = Path(args.viz_dir) if args.viz_dir else None

    # Generate report
    logger.info("Generating report...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_report(events_df, features_df, metadata, output_path, viz_dir)

    logger.info(f"✓ Report saved: {output_path}")
    logger.info("Report generation complete!")


if __name__ == "__main__":
    main()
