"""
thunder.utils
=============

Utility functions for thunder acoustics pipeline.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
import sys


def load_config(config_path: str | Path) -> Dict[str, Any]:
    """
    Load YAML configuration.

    Parameters
    ----------
    config_path : str or Path
        Path to config YAML file

    Returns
    -------
    config : dict
        Configuration dict

    Examples
    --------
    >>> config = load_config("configs/default.yaml")
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None:
    """
    Setup logging configuration.

    Parameters
    ----------
    log_level : str, default="INFO"
        Logging level (DEBUG, INFO, WARNING, ERROR)
    log_file : str, optional
        Log file path (None = console only)

    Examples
    --------
    >>> setup_logging(log_level="INFO", log_file="pipeline.log")
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(f"Logging configured: level={log_level}, file={log_file}")


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable string.

    Parameters
    ----------
    seconds : float
        Duration in seconds

    Returns
    -------
    formatted : str
        Formatted string

    Examples
    --------
    >>> print(format_duration(125.5))
    "2m 5.5s"
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def ensure_output_dir(output_dir: str | Path, date_prefix: bool = True) -> Path:
    """
    Ensure output directory exists.

    Parameters
    ----------
    output_dir : str or Path
        Base output directory
    date_prefix : bool, default=True
        Add YYYYMMDD prefix

    Returns
    -------
    final_dir : Path
        Final output directory path

    Examples
    --------
    >>> output_dir = ensure_output_dir("outputs", date_prefix=True)
    >>> print(output_dir)  # outputs/20251015
    """
    output_dir = Path(output_dir)

    if date_prefix:
        from datetime import datetime

        date_str = datetime.now().strftime("%Y%m%d")
        final_dir = output_dir / date_str
    else:
        final_dir = output_dir

    final_dir.mkdir(parents=True, exist_ok=True)
    return final_dir


def check_dependencies() -> Dict[str, bool]:
    """
    Check if external dependencies are available.

    Returns
    -------
    status : dict
        Dependency availability status

    Examples
    --------
    >>> status = check_dependencies()
    >>> if not status["ffmpeg"]:
    ...     print("ERROR: ffmpeg not found")
    """
    import shutil

    status = {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "yt-dlp": shutil.which("yt-dlp") is not None,
    }

    return status


def print_banner() -> None:
    """Print project banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     Thunder Acoustics in the Wild                    ║
    ║     v0.1.0                                            ║
    ║                                                       ║
    ║     Automated thunder acoustics analysis pipeline    ║
    ║     Research-grade • Reproducible • Open-source      ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)
