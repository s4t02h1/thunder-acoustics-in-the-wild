"""
thunder.metadata
================

Metadata handling and logging for research reproducibility.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def generate_video_id(url: str) -> str:
    """
    Generate unique video ID from URL.

    Parameters
    ----------
    url : str
        Video URL

    Returns
    -------
    video_id : str
        8-character hash

    Examples
    --------
    >>> video_id = generate_video_id("https://www.youtube.com/watch?v=example")
    """
    return hashlib.md5(url.encode()).hexdigest()[:8]


def create_metadata(
    source_url: str,
    config: dict,
    additional_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create metadata dict for an analysis run.

    Parameters
    ----------
    source_url : str
        Video source URL
    config : dict
        Analysis configuration
    additional_info : dict, optional
        Additional metadata fields

    Returns
    -------
    metadata : dict
        Complete metadata

    Examples
    --------
    >>> meta = create_metadata("https://...", config)
    """
    meta = {
        "source_url": source_url,
        "video_id": generate_video_id(source_url),
        "fetch_date": datetime.now().isoformat(),
        "analysis_timestamp": datetime.now().isoformat(),
        "config": config,
        "config_hash": hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "version": "0.1.0",
        "citation_required": True,
        "license": "MIT",
    }

    if additional_info:
        meta.update(additional_info)

    return meta


def save_metadata(metadata: Dict[str, Any], filepath: str | Path) -> None:
    """
    Save metadata to JSON file.

    Parameters
    ----------
    metadata : dict
        Metadata dict
    filepath : str or Path
        Output JSON path

    Examples
    --------
    >>> save_metadata(meta, "outputs/20251015/video/meta.json")
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"Metadata saved: {filepath}")


def load_metadata(filepath: str | Path) -> Dict[str, Any]:
    """
    Load metadata from JSON file.

    Parameters
    ----------
    filepath : str or Path
        Input JSON path

    Returns
    -------
    metadata : dict
        Loaded metadata

    Examples
    --------
    >>> meta = load_metadata("outputs/20251015/video/meta.json")
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Metadata file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    logger.info(f"Metadata loaded: {filepath}")
    return metadata


def verify_reproducibility(
    metadata1: Dict[str, Any], metadata2: Dict[str, Any]
) -> bool:
    """
    Verify if two runs used the same configuration.

    Parameters
    ----------
    metadata1, metadata2 : dict
        Metadata from two analysis runs

    Returns
    -------
    is_reproducible : bool
        True if config hashes match

    Examples
    --------
    >>> is_same = verify_reproducibility(meta1, meta2)
    """
    hash1 = metadata1.get("config_hash")
    hash2 = metadata2.get("config_hash")

    if hash1 is None or hash2 is None:
        logger.warning("Missing config hash in metadata")
        return False

    is_reproducible = hash1 == hash2
    logger.info(f"Reproducibility check: {is_reproducible}")
    return is_reproducible


def log_ethical_compliance(metadata: Dict[str, Any]) -> None:
    """
    Log ethical compliance information.

    Parameters
    ----------
    metadata : dict
        Metadata dict

    Examples
    --------
    >>> log_ethical_compliance(meta)
    """
    url = metadata.get("source_url", "Unknown")
    citation_required = metadata.get("citation_required", True)

    logger.info("=" * 60)
    logger.info("ETHICAL COMPLIANCE CHECK")
    logger.info("=" * 60)
    logger.info(f"Source: {url}")
    logger.info(f"Citation required: {citation_required}")
    logger.info("Usage:")
    logger.info("  ✓ Research purposes only")
    logger.info("  ✓ Respect copyright and terms of service")
    logger.info("  ✓ Cite original creator when publishing")
    logger.info("  ✓ No surveillance or privacy-invasive use")
    logger.info("=" * 60)
