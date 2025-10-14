#!/usr/bin/env python3
"""
fetch_videos.py

Download videos from URLs using yt-dlp.

Usage:
    python scripts/fetch_videos.py --url "https://youtube.com/watch?v=..." --output data/raw_videos/
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def fetch_video_ytdlp(
    url: str,
    output_dir: str | Path,
    format_spec: str = "best",
    max_retries: int = 3,
) -> dict | None:
    """
    Download video using yt-dlp.

    Parameters
    ----------
    url : str
        Video URL
    output_dir : str or Path
        Output directory
    format_spec : str, default="best"
        Video format (e.g., "best", "worst", "bestvideo+bestaudio")
    max_retries : int, default=3
        Maximum retry attempts

    Returns
    -------
    metadata : dict or None
        Video metadata (title, duration, id, etc.) or None if failed
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Output template: video_id.ext
    output_template = str(output_dir / "%(id)s.%(ext)s")

    # yt-dlp command
    cmd = [
        "yt-dlp",
        "--format",
        format_spec,
        "--output",
        output_template,
        "--no-playlist",  # Download single video only
        "--write-info-json",  # Save metadata
        "--retries",
        str(max_retries),
        url,
    ]

    logger.info(f"Fetching video: {url}")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        logger.info("✓ Video downloaded successfully")

        # Parse metadata from .info.json
        video_files = list(output_dir.glob("*.info.json"))
        if video_files:
            latest_meta_file = max(video_files, key=lambda p: p.stat().st_mtime)
            with open(latest_meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)

            return {
                "video_id": meta.get("id", "unknown"),
                "title": meta.get("title", "unknown"),
                "duration": meta.get("duration", 0),
                "uploader": meta.get("uploader", "unknown"),
                "upload_date": meta.get("upload_date", "unknown"),
                "source_url": url,
                "fetch_date": datetime.now().isoformat(),
            }
        else:
            logger.warning("Could not find metadata file")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp failed: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error(
            "yt-dlp not found. Install with: pip install yt-dlp "
            "or choco install yt-dlp (Windows)"
        )
        return None


def fetch_multiple_videos(
    url_file: str | Path,
    output_dir: str | Path,
    format_spec: str = "best",
    max_retries: int = 3,
) -> list[dict]:
    """
    Download multiple videos from a file.

    Parameters
    ----------
    url_file : str or Path
        Text file with one URL per line
    output_dir : str or Path
        Output directory
    format_spec : str, default="best"
        Video format
    max_retries : int, default=3
        Maximum retry attempts

    Returns
    -------
    results : list of dict
        List of metadata for each video
    """
    url_file = Path(url_file)
    if not url_file.exists():
        logger.error(f"URL file not found: {url_file}")
        return []

    with open(url_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    logger.info(f"Found {len(urls)} URLs in {url_file}")

    results = []
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Processing: {url}")
        meta = fetch_video_ytdlp(url, output_dir, format_spec, max_retries)
        if meta:
            results.append(meta)

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download videos using yt-dlp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single video
  python scripts/fetch_videos.py --url "https://youtube.com/watch?v=..." \\
      --output data/raw_videos/
  
  # Download from URL list
  python scripts/fetch_videos.py --url-file urls.txt --output data/raw_videos/
  
  # Custom format (best video + audio)
  python scripts/fetch_videos.py --url "..." --output data/raw_videos/ \\
      --format "bestvideo+bestaudio"
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Video URL")
    group.add_argument("--url-file", help="Text file with URLs (one per line)")

    parser.add_argument(
        "--output", required=True, help="Output directory for videos"
    )
    parser.add_argument(
        "--format",
        default="best",
        help="Video format (default: best)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts",
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

    # Download videos
    if args.url:
        meta = fetch_video_ytdlp(
            args.url, args.output, args.format, args.max_retries
        )
        success = meta is not None

        if success:
            # Save metadata
            meta_file = Path(args.output) / f"{meta['video_id']}_fetch.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Metadata saved: {meta_file}")

    else:  # url_file
        results = fetch_multiple_videos(
            args.url_file, args.output, args.format, args.max_retries
        )
        success = len(results) > 0

        if success:
            # Save summary
            summary_file = Path(args.output) / "fetch_summary.json"
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Summary saved: {summary_file}")
            logger.info(f"Successfully downloaded {len(results)} videos")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
