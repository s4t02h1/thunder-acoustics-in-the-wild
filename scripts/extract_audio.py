#!/usr/bin/env python3
"""
extract_audio.py

Extract audio from video files using ffmpeg.

Usage:
    python scripts/extract_audio.py --video path/to/video.mp4 --output path/to/audio.wav
"""

import argparse
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extract_audio_ffmpeg(
    video_path: str | Path,
    output_path: str | Path,
    sample_rate: int = 48000,
    bit_depth: int = 24,
    channels: int = 1,
    overwrite: bool = False,
) -> bool:
    """
    Extract audio from video using ffmpeg.

    Parameters
    ----------
    video_path : str or Path
        Input video file
    output_path : str or Path
        Output audio file (WAV)
    sample_rate : int, default=48000
        Target sample rate (Hz)
    bit_depth : int, default=24
        Bit depth (16, 24, or 32)
    channels : int, default=1
        Number of channels (1=mono, 2=stereo)
    overwrite : bool, default=False
        Overwrite existing file

    Returns
    -------
    success : bool
        True if extraction succeeded
    """
    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False

    if output_path.exists() and not overwrite:
        logger.error(f"Output file exists: {output_path}. Use --overwrite to replace.")
        return False

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Map bit depth to ffmpeg format
    bit_depth_map = {16: "s16", 24: "s24", 32: "s32"}
    sample_fmt = bit_depth_map.get(bit_depth, "s24")

    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",  # No video
        "-acodec",
        "pcm_" + sample_fmt + "le",  # PCM little-endian
        "-ar",
        str(sample_rate),  # Sample rate
        "-ac",
        str(channels),  # Channels
    ]

    if overwrite:
        cmd.append("-y")

    cmd.append(str(output_path))

    logger.info(f"Extracting audio: {video_path.name} → {output_path.name}")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        logger.info(f"✓ Audio extracted: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg failed: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(
            "ffmpeg not found. Install with: choco install ffmpeg (Windows) "
            "or brew install ffmpeg (macOS)"
        )
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract audio from video using ffmpeg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract audio with defaults (48kHz, 24-bit, mono)
  python scripts/extract_audio.py --video video.mp4 --output audio.wav
  
  # Custom sample rate and stereo
  python scripts/extract_audio.py --video video.mp4 --output audio.wav \\
      --sample-rate 44100 --channels 2
  
  # Overwrite existing file
  python scripts/extract_audio.py --video video.mp4 --output audio.wav --overwrite
        """,
    )

    parser.add_argument("--video", required=True, help="Input video file")
    parser.add_argument("--output", required=True, help="Output audio file (WAV)")
    parser.add_argument(
        "--sample-rate", type=int, default=48000, help="Sample rate (Hz, default: 48000)"
    )
    parser.add_argument(
        "--bit-depth",
        type=int,
        default=24,
        choices=[16, 24, 32],
        help="Bit depth (default: 24)",
    )
    parser.add_argument(
        "--channels", type=int, default=1, choices=[1, 2], help="Channels (1=mono, 2=stereo)"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing output file"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Extract audio
    success = extract_audio_ffmpeg(
        video_path=args.video,
        output_path=args.output,
        sample_rate=args.sample_rate,
        bit_depth=args.bit_depth,
        channels=args.channels,
        overwrite=args.overwrite,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
