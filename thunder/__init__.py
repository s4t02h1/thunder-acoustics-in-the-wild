"""
Thunder Acoustics in the Wild
==============================

Automated thunder acoustics analysis pipeline from web videos.

Modules:
    io: Audio I/O operations
    preprocess: Noise reduction and filtering
    detection: Thunder event detection
    features: Acoustic feature extraction
    distance: Distance estimation from flash-to-thunder delay
    metadata: Metadata handling and logging
    utils: Utility functions
"""

__version__ = "0.1.0"
__author__ = "s4t02h1"
__license__ = "MIT"

from thunder import io, preprocess, detection, features, distance, metadata, utils

__all__ = [
    "io",
    "preprocess",
    "detection",
    "features",
    "distance",
    "metadata",
    "utils",
]
