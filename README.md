# Thunder Acoustics in the Wild

**Automated thunder acoustics analysis pipeline from web videos for research purposes**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Project Goals

Extract and analyze thunder acoustics from publicly available web videos to build a **reproducible, extensible, and automated research pipeline** for:

- **Acoustic characterization** of thunder events (time-domain, frequency-domain, time-frequency)
- **Event detection** and classification (IC: intra-cloud, CG: cloud-to-ground)
- **Distance estimation** from lightning flash to thunder arrival time (Δt → d ≈ c_air × Δt)
- **Statistical analysis** for atmospheric electricity and meteorology research

### Research-Grade Principles

- ✅ **100% scripted**: Makefile, CLI, Notebooks
- ✅ **Open-source dependencies**: ffmpeg, yt-dlp, numpy, scipy, librosa
- ✅ **Reproducible**: All outputs timestamped, metadata logged (JSON/CSV)
- ✅ **Ethical**: License/copyright/citation/usage tracking mandatory

---

## 📁 Project Structure

```
thunder-acoustics-in-the-wild/
├── data/
│   ├── raw_videos/       # Downloaded videos (gitignored)
│   ├── raw_audio/        # Extracted audio (WAV, 48kHz/24bit)
│   ├── interim/          # Intermediate processing
│   └── processed/        # Final cleaned audio
├── thunder/              # Python package
│   ├── __init__.py
│   ├── io.py            # Audio I/O
│   ├── preprocess.py    # Noise reduction, filtering
│   ├── detection.py     # Event detection
│   ├── features.py      # Feature extraction
│   ├── distance.py      # Distance estimation
│   ├── metadata.py      # Metadata handling
│   └── utils.py         # Utilities
├── scripts/              # CLI tools
│   ├── fetch_videos.py
│   ├── extract_audio.py
│   ├── detect_events.py
│   ├── compute_features.py
│   ├── visualize.py
│   └── build_report.py
├── notebooks/            # Jupyter notebooks
│   ├── 00_quickstart.ipynb
│   ├── 10_event_detection_eval.ipynb
│   └── 20_features_scouting.ipynb
├── configs/
│   └── default.yaml      # Default analysis parameters
├── outputs/              # Results (YYYYMMDD/<video_id>/)
├── docs/                 # Documentation
├── tests/                # Unit tests
├── pyproject.toml        # Project metadata
├── requirements.txt      # Dependencies
├── Makefile              # Build automation
└── README.md             # This file
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+**
2. **ffmpeg** (audio extraction)
3. **yt-dlp** (video download)

#### Windows

```powershell
# Install ffmpeg and yt-dlp via Chocolatey
choco install ffmpeg yt-dlp

# Or download manually:
# ffmpeg: https://ffmpeg.org/download.html
# yt-dlp: https://github.com/yt-dlp/yt-dlp/releases
```

#### macOS

```bash
brew install ffmpeg yt-dlp
```

#### Linux

```bash
sudo apt install ffmpeg
pip install yt-dlp
```

### Installation

#### Option 1: Automated Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/s4t02h1/thunder-acoustics-in-the-wild.git
cd thunder-acoustics-in-the-wild

# Setup everything (venv + deps + dependency check)
make setup
```

**What `make setup` does:**
- Creates Python virtual environment (`.venv/`)
- Installs all Python dependencies
- Checks for `ffmpeg` and `yt-dlp` availability
- Auto-installs `yt-dlp` if missing
- Appends installation guide to README if `ffmpeg` is missing

#### Option 2: Manual Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\activate

# Activate (Unix/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Verify external dependencies
make check-deps
```

### Demo Pipeline

Run the full pipeline on a sample video:

```bash
# Windows PowerShell
make demo

# Unix/macOS
make demo
```

**What `make demo` does:**
1. Writes sample YouTube URL to `data/urls.txt`
2. Downloads video to `data/raw_videos/`
3. Extracts audio (48kHz, 24-bit, mono) → `data/raw_audio/demo.wav`
4. Detects thunder events → `outputs/YYYYMMDD/demo/events.csv`
5. Computes acoustic features → `outputs/YYYYMMDD/demo/features.csv`
6. Generates visualizations → `outputs/YYYYMMDD/demo/viz/`
7. Builds Markdown report → `outputs/YYYYMMDD/demo/report.md`

Output: `outputs/YYYYMMDD/demo/report.md`

### Makefile Targets

```bash
make setup       # Setup venv + install deps + check ffmpeg/yt-dlp
make check-deps  # Verify ffmpeg and yt-dlp availability
make ingest      # Download videos from data/urls.txt
make extract     # Extract audio from all videos in data/raw_videos
make mvp         # Process single audio file (detect + features + viz + report)
make demo        # Full pipeline with sample URL
make test        # Run pytest
make lint        # Run flake8
make format      # Run black formatter
make notebooks   # Start Jupyter Lab
make clean       # Remove build artifacts
```

### Windows-Specific Notes

- **PowerShell Execution Policy**: If you get script execution errors, run:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

- **Path Issues**: If `yt-dlp` is not found after pip install, add `.venv\Scripts` to PATH:
  ```powershell
  $env:PATH = ".venv\Scripts;$env:PATH"
  ```

- **ffmpeg Installation**: The `check_deps.ps1` script will append installation instructions to README if ffmpeg is missing.

---

## 📊 Features & Metrics

### Event Detection

- **Energy-based threshold** with spectral change confirmation
- **Adaptive windowing** (configurable: 50ms–500ms)
- **Event merging** for closely spaced thunderclaps

### Acoustic Features

#### Time Domain
- **Peak amplitude**, RMS, Crest factor
- **Zero-crossing rate**
- **Attack/decay time**

#### Frequency Domain
- **Spectral centroid**, bandwidth, rolloff
- **Spectral slope** (low-frequency dominance indicator)
- **Dominant frequency**

#### Time-Frequency
- **STFT** (Short-Time Fourier Transform)
- **CWT** (Continuous Wavelet Transform)
- **Mel-frequency cepstral coefficients (MFCC)**

#### Statistical
- **Kurtosis**, skewness
- **Energy distribution** across bands (20–100Hz, 100–500Hz, 500–6000Hz)

### Distance Estimation

From flash-to-thunder delay:

```
d ≈ c_air × Δt
```

where:
- `c_air ≈ 343 m/s @ 20°C` (temperature-corrected)
- `Δt`: time between visual flash and thunder onset (manual annotation or video analysis)

---

## 🛠️ Usage

### 1. Fetch Videos

```bash
python scripts/fetch_videos.py \
    --urls urls.txt \
    --output data/raw_videos
```

`urls.txt` format:
```
https://www.youtube.com/watch?v=example1
https://www.youtube.com/watch?v=example2
```

### 2. Extract Audio

```bash
python scripts/extract_audio.py \
    --video data/raw_videos/video.mp4 \
    --output data/raw_audio/video.wav \
    --sample-rate 48000 \
    --bit-depth 24 \
    --channels 1
```

### 3. Detect Events

```bash
python scripts/detect_events.py \
    --audio data/raw_audio/video.wav \
    --config configs/default.yaml \
    --output outputs/20251015/video/events.csv
```

### 4. Compute Features

```bash
python scripts/compute_features.py \
    --audio data/raw_audio/video.wav \
    --events outputs/20251015/video/events.csv \
    --output outputs/20251015/video/features.csv
```

### 5. Visualize

```bash
python scripts/visualize.py \
    --audio data/raw_audio/video.wav \
    --events outputs/20251015/video/events.csv \
    --output outputs/20251015/video/plots
```

Generates:
- `waveform.png`
- `spectrogram.png`
- `event_features_histogram.png`

### 6. Build Report

```bash
python scripts/build_report.py \
    --input outputs/20251015/video \
    --output outputs/20251015/video/report.md
```

---

## ⚙️ Configuration

Configuration is stored in `configs/default.yaml` with multiple sections:

### Audio Settings

```yaml
audio:
  sample_rate: 48000        # Hz - Standard high-quality audio
  bit_depth: 24             # bits - Professional audio quality
  channels: 1               # mono (thunder is omnidirectional)
  highpass_hz: 20           # Hz - Remove subsonic noise
  lowpass_hz: 6000          # Hz - Thunder energy upper limit
  normalize: true           # Apply RMS normalization
```

### Detection Parameters

```yaml
detect:
  frame_len_ms: 20          # ms - Analysis frame length
  hop_len_ms: 10            # ms - Frame hop (50% overlap)
  energy_thresh_db: -25     # dB - Minimum energy for detection
  merge_gap_ms: 300         # ms - Merge events closer than this
  min_event_ms: 150         # ms - Discard events shorter than this
  spectral_change_thresh: 0.25  # Normalized spectral flux threshold
```

### Feature Extraction

```yaml
features:
  stft_win_ms: 64           # ms - STFT window length
  stft_hop_ms: 16           # ms - STFT hop length
  n_mels: 64                # Number of mel bands
  mfcc_n: 13                # Number of MFCC coefficients
  cwt_wavelet: "morlet"     # Continuous wavelet transform wavelet
```

### Visualization

```yaml
viz:
  spectrogram_db_range: 80  # dB - Dynamic range for spectrogram
  dpi: 160                  # DPI for figure output
```

### Distance Estimation

```yaml
distance:
  enable_flash_alignment: true  # Detect lightning flash from video
  speed_of_sound: 343.5     # m/s @ 20°C (331.5 + 0.6 * T)
  reference_temp: 20        # Celsius
```

### Configuration Tools

```bash
# Validate configuration
python scripts/validate_config.py --config configs/default.yaml

# Migrate old config to new format
python scripts/migrate_config.py --input configs/old.yaml --output configs/new.yaml
```

**Validation checks:**
- Sample rate validity and Nyquist limit
- Frequency range consistency
- Frame/hop overlap ratios
- Threshold reasonableness
- STFT parameter alignment
- Temperature-dependent speed of sound formula

---

## 📓 Notebooks

### `00_quickstart.ipynb`

End-to-end pipeline walkthrough on a single video.

### `10_event_detection_eval.ipynb`

Sensitivity analysis for detection thresholds.

### `20_features_scouting.ipynb`

Feature correlation and visualization.

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=thunder --cov-report=html
```

---

## 📐 Scientific Validity

### Event Detection Validation

- **Manual annotation** of 10+ videos for ground truth
- **Precision/Recall/F1** metrics reported in `docs/validation.md`

### Noise Robustness

- **SNR variation tests** (wind, rain, traffic)
- Feature stability across noise levels

### Reproducibility

- **Config versioning**: All parameters logged in `meta.json`
- **Hash verification**: Audio checksums for re-run validation

### Distance Estimation Accuracy

- **Flash-to-thunder Δt**: Manual annotation from video
- **Temperature correction**: c_air = 331.3 + 0.606 × T (m/s, T in °C)
- **Error analysis**: Terrain/wind/refraction effects documented

---

## ⚠️ Limitations & Ethics

### Acoustic Limitations

- ❌ **ELF/VLF electromagnetic phenomena** not captured (requires specialized receivers)
- ❌ **Far-field approximations** break down for complex terrain
- ⚠️ **Compressed video audio** may have codec artifacts

### Noise Sources

- Wind, rain, traffic, indoor reverberation
- Microphone overload on close strikes

### Ethical Considerations

- ✅ **Respect copyright**: Cite original video creators
- ✅ **No surveillance**: Do not apply to privacy-invasive scenarios
- ✅ **Research approval**: Obtain IRB/ethics board approval if needed
- ✅ **Data retention**: Follow GDPR/local laws for storage limits

See `LICENSE` for full usage terms.

---

## 🔬 Research Applications

- **Meteorology**: Storm cell characterization
- **Atmospheric electricity**: IC/CG discrimination
- **Geophysics**: Infrasound coupling studies
- **Machine learning**: Acoustic event classification

### Future Extensions

- **Multi-channel analysis** (stereo localization)
- **Deep learning classifiers** (BiLSTM, CNN on spectrograms)
- **Weather metadata integration** (NOAA, ECMWF APIs)
- **Real-time streaming** (WebSocket + edge deployment)

---

## 📚 References

### Key Papers

- Uman, M. A. (2001). *The Lightning Discharge*. Dover.
- Rakov, V. A., & Uman, M. A. (2003). *Lightning: Physics and Effects*. Cambridge.
- Few, A. A. (1985). "The Production of Lightning-Associated Infrasonic Acoustic Sources in Thunderclouds." *Journal of Geophysical Research*.

### Software

- [librosa](https://librosa.org/) - Audio feature extraction
- [ffmpeg](https://ffmpeg.org/) - Multimedia framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader

---

## 🤝 Contributing

Contributions welcome! See `docs/CONTRIBUTING.md` for guidelines.

**Before submitting:**
- Run `make test` and `make lint`
- Update documentation
- Add unit tests for new features

---

## 📄 License

MIT License - see `LICENSE` for details.

**Citation:**

```bibtex
@software{thunder_acoustics_2025,
  author = {s4t02h1},
  title = {Thunder Acoustics in the Wild},
  year = {2025},
  url = {https://github.com/s4t02h1/thunder-acoustics-in-the-wild}
}
```

---

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/s4t02h1/thunder-acoustics-in-the-wild/issues)
- **Discussions**: [GitHub Discussions](https://github.com/s4t02h1/thunder-acoustics-in-the-wild/discussions)

---

**Status**: 🚧 Alpha - Under active development

**Last updated**: 2025-10-15
