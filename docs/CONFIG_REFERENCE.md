# Thunder Acoustics Configuration Quick Reference

## 📋 Configuration Sections

### 1. Audio (`audio`)

Basic audio processing parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sample_rate` | int | 48000 | Sample rate in Hz |
| `bit_depth` | int | 24 | Bit depth (16, 24, 32) |
| `channels` | int | 1 | Number of channels (1=mono) |
| `highpass_hz` | int | 20 | Highpass filter cutoff (Hz) |
| `lowpass_hz` | int | 6000 | Lowpass filter cutoff (Hz) |
| `normalize` | bool | true | Apply RMS normalization |

**Typical Thunder Frequency Range**: 20-6000 Hz (peak energy: 50-500 Hz)

---

### 2. Detection (`detect`)

Event detection parameters (in milliseconds):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frame_len_ms` | int | 20 | Analysis frame length (ms) |
| `hop_len_ms` | int | 10 | Frame hop length (ms) |
| `energy_thresh_db` | float | -25 | Energy threshold (dB) |
| `merge_gap_ms` | int | 300 | Merge events closer than this (ms) |
| `min_event_ms` | int | 150 | Minimum event duration (ms) |
| `spectral_change_thresh` | float | 0.25 | Spectral flux threshold (0-1) |

**Recommended Ranges**:
- Frame overlap: 50-75% (frame_len - hop_len) / frame_len
- Energy threshold: -40 to -15 dB (lower = more sensitive)
- Merge gap: 200-500 ms (thunderclaps often have multiple peaks)
- Min event: 100-300 ms (filter out transients)

---

### 3. Features (`features`)

Feature extraction parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stft_win_ms` | int | 64 | STFT window length (ms) |
| `stft_hop_ms` | int | 16 | STFT hop length (ms) |
| `n_mels` | int | 64 | Number of mel filterbanks |
| `mfcc_n` | int | 13 | Number of MFCC coefficients |
| `cwt_wavelet` | str | "morlet" | Wavelet type for CWT |

**Time-Frequency Analysis**:
- STFT: Good for broadband signals like thunder
- CWT: Better for transient events
- MFCC: Compact representation for classification

**Computed Values** (@ 48kHz):
- 64ms window = 3072 samples ≈ 2048 n_fft (nearest power of 2)
- 16ms hop = 768 samples ≈ 512 hop_length
- Overlap = 75%

---

### 4. Visualization (`viz`)

Plotting parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `spectrogram_db_range` | int | 80 | Dynamic range (dB) |
| `dpi` | int | 160 | Output resolution |

---

### 5. Distance (`distance`)

Distance estimation from lightning flash:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_flash_alignment` | bool | true | Enable flash detection |
| `speed_of_sound` | float | 343.5 | Sound speed (m/s) |
| `reference_temp` | int | 20 | Reference temperature (°C) |

**Formula**: `c_air = 331.5 + 0.6 × T` (m/s, T in °C)

**Distance calculation**: `d ≈ c_air × Δt`
- Δt: Time between flash and thunder (seconds)
- d: Distance in meters
- Example: 3 seconds delay @ 20°C → ~1 km

---

## 🔧 Configuration Validation

```bash
# Validate current config
python scripts/validate_config.py --config configs/default.yaml

# Output as JSON
python scripts/validate_config.py --config configs/default.yaml --json
```

**Validation checks**:
- ✓ Sample rate vs. Nyquist limit
- ✓ Frequency range consistency (highpass < lowpass)
- ✓ Frame overlap ratio (recommend 50-75%)
- ✓ Energy threshold reasonableness (-50 to -10 dB)
- ✓ STFT n_fft alignment with window samples
- ✓ Speed of sound formula consistency

---

## 🔄 Configuration Migration

Convert old config format to new format:

```bash
python scripts/migrate_config.py \
    --input configs/old.yaml \
    --output configs/new.yaml
```

**What gets migrated**:
- `preprocessing` → `audio` (seconds → milliseconds conversion)
- `detection` → `detect` (seconds → milliseconds)
- STFT samples → milliseconds calculation
- Adds new sections: `viz`, enhanced `distance`

---

## 📊 Example Configurations

### High Sensitivity (Distant Thunder)

```yaml
detect:
  energy_thresh_db: -35     # Lower threshold
  merge_gap_ms: 500         # Longer merge window
  min_event_ms: 100         # Accept shorter events
```

### Low Noise (Close Thunder)

```yaml
detect:
  energy_thresh_db: -15     # Higher threshold
  merge_gap_ms: 200         # Shorter merge window
  min_event_ms: 200         # Filter transients
```

### High-Resolution Analysis

```yaml
features:
  stft_win_ms: 128          # Longer window → better freq resolution
  stft_hop_ms: 32           # 75% overlap maintained
  n_mels: 128               # More mel bands
  mfcc_n: 20                # More coefficients
```

### Fast Processing

```yaml
features:
  stft_win_ms: 32           # Shorter window
  stft_hop_ms: 16           # 50% overlap
  n_mels: 40                # Fewer mel bands
  mfcc_n: 10                # Fewer coefficients
```

---

## 🎯 Parameter Tuning Tips

### Detection Threshold

Start with default `-25 dB`, then adjust:
- **Too many false positives** (wind, traffic): Increase to `-20 dB` or `-15 dB`
- **Missing thunder events**: Decrease to `-30 dB` or `-35 dB`

Test on labeled data:
```bash
# Run sensitivity analysis notebook
jupyter notebook notebooks/10_event_detection_eval.ipynb
```

### Merge Gap

- **Short gap (100-200ms)**: Treats each rumble peak as separate event
- **Long gap (500-1000ms)**: Merges entire thunderclap into one event

Depends on analysis goal:
- Peak counting → short gap
- Total energy per thunderclap → long gap

### STFT Window

Trade-off between time and frequency resolution:
- **Longer window (128ms)**: Better frequency resolution, worse time localization
- **Shorter window (32ms)**: Better time resolution, worse frequency resolution

Thunder guideline: 64ms is good balance (≈16 Hz frequency bins @ 48kHz)

---

## 📚 References

- **Thunder acoustics**: Uman (2001), "The Lightning Discharge"
- **STFT**: Oppenheim & Schafer, "Discrete-Time Signal Processing"
- **MFCC**: Davis & Mermelstein (1980), "Comparison of Parametric Representations"

---

**Last Updated**: 2025-10-15  
**Config Version**: 1.0
