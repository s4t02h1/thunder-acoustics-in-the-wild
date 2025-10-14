#!/usr/bin/env python3
"""
visualize.py

Generate visualizations for thunder analysis.

Usage:
    python scripts/visualize.py --audio audio.wav --events events.csv --output-dir outputs/
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from thunder import io, utils


def plot_waveform_with_events(
    audio: np.ndarray,
    sr: int,
    events: list[dict],
    output_path: str | Path,
    dpi: int = 300,
    figsize: tuple = (12, 4),
):
    """
    Plot waveform with detected events highlighted.

    Parameters
    ----------
    audio : ndarray
        Audio signal
    sr : int
        Sample rate
    events : list of dict
        Detected events with 'start' and 'end' times
    output_path : str or Path
        Output PNG file
    dpi : int, default=300
        Resolution
    figsize : tuple, default=(12, 4)
        Figure size (width, height)
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Time axis
    time = np.arange(len(audio)) / sr

    # Plot waveform
    ax.plot(time, audio, color="steelblue", linewidth=0.5, label="Waveform")

    # Highlight events
    for i, event in enumerate(events):
        ax.axvspan(
            event["start"],
            event["end"],
            alpha=0.3,
            color="red",
            label="Thunder Event" if i == 0 else "",
        )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Audio Waveform with Detected Thunder Events")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def plot_spectrogram_with_events(
    audio: np.ndarray,
    sr: int,
    events: list[dict],
    output_path: str | Path,
    n_fft: int = 2048,
    hop_length: int = 512,
    dpi: int = 300,
    figsize: tuple = (12, 6),
    vmin: float = -80,
    vmax: float = 0,
    freq_range: tuple = (20, 6000),
):
    """
    Plot spectrogram with detected events marked.

    Parameters
    ----------
    audio : ndarray
        Audio signal
    sr : int
        Sample rate
    events : list of dict
        Detected events
    output_path : str or Path
        Output PNG file
    n_fft : int, default=2048
        FFT size
    hop_length : int, default=512
        Hop length
    dpi : int, default=300
        Resolution
    figsize : tuple, default=(12, 6)
        Figure size
    vmin : float, default=-80
        Minimum dB
    vmax : float, default=0
        Maximum dB
    freq_range : tuple, default=(20, 6000)
        Frequency range (Hz)
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Compute STFT
    from scipy.signal import stft

    f, t, Zxx = stft(audio, fs=sr, nperseg=n_fft, noverlap=n_fft - hop_length)

    # Convert to dB
    magnitude = np.abs(Zxx)
    magnitude_db = 20 * np.log10(magnitude + 1e-10)

    # Plot spectrogram
    im = ax.pcolormesh(
        t, f, magnitude_db, shading="auto", cmap="viridis", vmin=vmin, vmax=vmax
    )

    # Mark events
    for event in events:
        ax.axvline(event["start"], color="red", linestyle="--", linewidth=1, alpha=0.7)
        ax.axvline(event["end"], color="red", linestyle="--", linewidth=1, alpha=0.7)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Spectrogram with Thunder Events")
    ax.set_yscale("log")
    ax.set_ylim(freq_range)
    ax.grid(True, alpha=0.3, which="both")

    cbar = plt.colorbar(im, ax=ax, label="Magnitude (dB)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def plot_feature_histograms(
    features_df: pd.DataFrame,
    output_path: str | Path,
    dpi: int = 300,
    figsize: tuple = (12, 8),
):
    """
    Plot histograms of extracted features.

    Parameters
    ----------
    features_df : DataFrame
        Features dataframe
    output_path : str or Path
        Output PNG file
    dpi : int, default=300
        Resolution
    figsize : tuple, default=(12, 8)
        Figure size
    """
    # Select numeric columns (exclude event_id, MFCC arrays, etc.)
    numeric_cols = features_df.select_dtypes(include=["number"]).columns
    exclude = ["event_id", "start", "end", "duration"]
    plot_cols = [c for c in numeric_cols if c not in exclude]

    n_features = len(plot_cols)
    n_cols = 3
    n_rows = (n_features + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    axes = axes.flatten()

    for i, col in enumerate(plot_cols):
        ax = axes[i]
        data = features_df[col].dropna()

        if len(data) > 0:
            ax.hist(data, bins=20, color="steelblue", edgecolor="black", alpha=0.7)
            ax.set_title(col, fontsize=10)
            ax.set_xlabel("Value")
            ax.set_ylabel("Count")
            ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for i in range(n_features, len(axes)):
        axes[i].axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate visualizations for thunder analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all visualizations
  python scripts/visualize.py --audio audio.wav --events events.csv \\
      --output-dir outputs/viz/
  
  # With features
  python scripts/visualize.py --audio audio.wav --events events.csv \\
      --features features.csv --output-dir outputs/viz/
        """,
    )

    parser.add_argument("--audio", required=True, help="Input audio file (WAV)")
    parser.add_argument("--events", required=True, help="Input events CSV")
    parser.add_argument("--features", help="Input features CSV (optional)")
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for plots"
    )
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
    config = utils.load_config(args.config)
    viz_config = config.get("visualization", {})

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load audio
    logger.info(f"Loading audio: {args.audio}")
    audio, sr = io.load_audio(args.audio)

    # Load events
    logger.info(f"Loading events: {args.events}")
    events_df = pd.read_csv(args.events)
    events = events_df.to_dict("records")
    logger.info(f"Found {len(events)} events")

    # Plot waveform
    logger.info("Plotting waveform...")
    waveform_path = output_dir / "waveform.png"
    plot_waveform_with_events(
        audio,
        sr,
        events,
        waveform_path,
        dpi=viz_config.get("dpi", 300),
        figsize=tuple(viz_config.get("figsize", [12, 4])),
    )
    logger.info(f"✓ Waveform saved: {waveform_path}")

    # Plot spectrogram
    logger.info("Plotting spectrogram...")
    spec_path = output_dir / "spectrogram.png"
    spec_config = viz_config.get("spectrogram", {})
    plot_spectrogram_with_events(
        audio,
        sr,
        events,
        spec_path,
        n_fft=spec_config.get("n_fft", 2048),
        hop_length=spec_config.get("hop_length", 512),
        dpi=viz_config.get("dpi", 300),
        figsize=tuple(viz_config.get("figsize", [12, 6])),
        vmin=spec_config.get("vmin", -80),
        vmax=spec_config.get("vmax", 0),
        freq_range=(
            spec_config.get("freq_min", 20),
            spec_config.get("freq_max", 6000),
        ),
    )
    logger.info(f"✓ Spectrogram saved: {spec_path}")

    # Plot feature histograms
    if args.features:
        logger.info(f"Loading features: {args.features}")
        features_df = pd.read_csv(args.features)

        logger.info("Plotting feature histograms...")
        hist_path = output_dir / "feature_histograms.png"
        plot_feature_histograms(
            features_df,
            hist_path,
            dpi=viz_config.get("dpi", 300),
            figsize=(12, 8),
        )
        logger.info(f"✓ Histograms saved: {hist_path}")

    logger.info("Visualization complete!")


if __name__ == "__main__":
    main()
