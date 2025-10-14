# batch_extract.py
# Batch extract audio from all videos in data/raw_videos (Windows)

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thunder import utils
import subprocess

def batch_extract_audio(
    video_dir: Path,
    audio_dir: Path,
    sample_rate: int = 48000,
    bit_depth: int = 24,
    channels: int = 1,
):
    """
    Extract audio from all videos in a directory.

    Parameters
    ----------
    video_dir : Path
        Directory containing video files
    audio_dir : Path
        Output directory for audio files
    sample_rate : int
        Target sample rate
    bit_depth : int
        Bit depth (16, 24, 32)
    channels : int
        Number of channels
    """
    logger = logging.getLogger(__name__)
    
    # Create output directory
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all video files
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.webm']
    video_files = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f'*{ext}'))
    
    if not video_files:
        logger.warning(f"No video files found in {video_dir}")
        return
    
    logger.info(f"Found {len(video_files)} video files")
    
    # Extract audio from each video
    for i, video_path in enumerate(video_files, 1):
        audio_path = audio_dir / f"{video_path.stem}.wav"
        
        logger.info(f"[{i}/{len(video_files)}] Extracting: {video_path.name}")
        
        # Build ffmpeg command
        bit_depth_map = {16: "s16", 24: "s24", 32: "s32"}
        sample_fmt = bit_depth_map.get(bit_depth, "s24")
        
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", f"pcm_{sample_fmt}le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            "-y",  # Overwrite
            str(audio_path),
        ]
        
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            logger.info(f"  ✓ Saved: {audio_path.name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"  ✗ Failed: {e.stderr}")
        except FileNotFoundError:
            logger.error("  ✗ ffmpeg not found")
            break

def main():
    """CLI entry point."""
    utils.setup_logging(log_level='INFO')
    logger = logging.getLogger(__name__)
    
    # Load config
    config_path = Path(__file__).parent.parent.parent / 'configs' / 'default.yaml'
    config = utils.load_config(config_path)
    
    # Paths
    video_dir = Path('data/raw_videos')
    audio_dir = Path('data/raw_audio')
    
    # Extract
    preprocess_config = config.get('preprocessing', {})
    batch_extract_audio(
        video_dir,
        audio_dir,
        sample_rate=preprocess_config.get('sample_rate', 48000),
        bit_depth=preprocess_config.get('bit_depth', 24),
        channels=preprocess_config.get('channels', 1),
    )
    
    logger.info("Batch extraction complete!")


if __name__ == "__main__":
    main()
