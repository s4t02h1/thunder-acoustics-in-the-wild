# Makefile for thunder-acoustics-in-the-wild
# Requires: Python 3.11+, ffmpeg, yt-dlp
# OS Detection
ifeq ($(OS),Windows_NT)
	PYTHON := python
	VENV_ACTIVATE := .venv\Scripts\activate
	MKDIR := if not exist
	RM := rmdir /s /q
	DATE := powershell -Command "Get-Date -Format yyyyMMdd"
	CHECK_SCRIPT := powershell -ExecutionPolicy Bypass -File scripts\win\check_deps.ps1
else
	PYTHON := python3
	VENV_ACTIVATE := .venv/bin/activate
	MKDIR := mkdir -p
	RM := rm -rf
	DATE := date +%Y%m%d
	CHECK_SCRIPT := bash scripts/unix/check_deps.sh
endif

.PHONY: help setup install check-deps validate-config ingest extract mvp demo clean test lint format notebooks

# Default target
help:
	@echo "thunder-acoustics-in-the-wild - Makefile targets"
	@echo "=================================================="
	@echo "setup        : Create venv + install dependencies + check ffmpeg/yt-dlp"
	@echo "install      : Install Python dependencies (requires venv)"
	@echo "check-deps   : Verify ffmpeg and yt-dlp are installed"
	@echo "validate-config : Validate configuration file"
	@echo "ingest       : Download videos from data/urls.txt"
	@echo "extract      : Extract audio from all videos in data/raw_videos"
	@echo "mvp          : Process single audio file (detect + features + viz + report)"
	@echo "demo         : Complete pipeline on sample URL"
	@echo "test         : Run pytest"
	@echo "lint         : Run flake8"
	@echo "format       : Run black formatter"
	@echo "clean        : Remove generated files"
	@echo "notebooks    : Start Jupyter lab"

# Setup: Create venv + install + check deps
setup:
	@echo "Setting up environment..."
	$(PYTHON) -m venv .venv
	@echo "Installing dependencies..."
ifeq ($(OS),Windows_NT)
	.venv\Scripts\pip install --upgrade pip
	.venv\Scripts\pip install -r requirements.txt
	.venv\Scripts\pip install -e .
else
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .
endif
	@echo "Checking external dependencies..."
	@$(CHECK_SCRIPT)

# Install dependencies (assumes venv exists)
install:
ifeq ($(OS),Windows_NT)
	.venv\Scripts\pip install -r requirements.txt
	.venv\Scripts\pip install -e .
else
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .
endif

# Check external dependencies
check-deps:
	@$(CHECK_SCRIPT)

# Validate configuration
validate-config:
	@echo "Validating configuration..."
ifeq ($(OS),Windows_NT)
	.venv\Scripts\python scripts\validate_config.py --config configs\default.yaml
else
	.venv/bin/python scripts/validate_config.py --config configs/default.yaml
endif

# Ingest: Download videos from data/urls.txt
ingest: check-deps
	@echo "Downloading videos from data/urls.txt..."
ifeq ($(OS),Windows_NT)
	@if not exist data\urls.txt (echo ERROR: data\urls.txt not found && exit /b 1)
	.venv\Scripts\python scripts\fetch_videos.py --url-file data\urls.txt --output data\raw_videos
else
	@test -f data/urls.txt || (echo "ERROR: data/urls.txt not found" && exit 1)
	.venv/bin/python scripts/fetch_videos.py --url-file data/urls.txt --output data/raw_videos
endif
	@echo "✓ Videos downloaded to data/raw_videos"

# Extract: Extract audio from all videos
extract: check-deps
	@echo "Extracting audio from videos..."
ifeq ($(OS),Windows_NT)
	.venv\Scripts\python scripts\win\batch_extract.py
else
	.venv/bin/python scripts/unix/batch_extract.py
endif
	@echo "✓ Audio extracted to data/raw_audio"

# MVP: Process single audio file
mvp:
	@echo "Running MVP pipeline..."
ifeq ($(OS),Windows_NT)
	@set DATESTAMP=$(shell powershell -Command "Get-Date -Format yyyyMMdd") && \
	if not exist data\raw_audio\demo.wav (echo ERROR: data\raw_audio\demo.wav not found && exit /b 1) && \
	if not exist outputs\%DATESTAMP%\demo mkdir outputs\%DATESTAMP%\demo && \
	.venv\Scripts\python scripts\detect_events.py --audio data\raw_audio\demo.wav --output outputs\%DATESTAMP%\demo\events.csv && \
	.venv\Scripts\python scripts\compute_features.py --audio data\raw_audio\demo.wav --events outputs\%DATESTAMP%\demo\events.csv --output outputs\%DATESTAMP%\demo\features.csv && \
	.venv\Scripts\python scripts\visualize.py --audio data\raw_audio\demo.wav --events outputs\%DATESTAMP%\demo\events.csv --features outputs\%DATESTAMP%\demo\features.csv --output-dir outputs\%DATESTAMP%\demo\viz && \
	.venv\Scripts\python scripts\build_report.py --events outputs\%DATESTAMP%\demo\events.csv --features outputs\%DATESTAMP%\demo\features.csv --meta outputs\%DATESTAMP%\demo\meta.json --viz-dir outputs\%DATESTAMP%\demo\viz --output outputs\%DATESTAMP%\demo\report.md && \
	echo ✓ MVP complete! Check outputs\%DATESTAMP%\demo\report.md
else
	@DATESTAMP=$$(date +%Y%m%d) && \
	test -f data/raw_audio/demo.wav || (echo "ERROR: data/raw_audio/demo.wav not found" && exit 1) && \
	mkdir -p outputs/$$DATESTAMP/demo && \
	.venv/bin/python scripts/detect_events.py --audio data/raw_audio/demo.wav --output outputs/$$DATESTAMP/demo/events.csv && \
	.venv/bin/python scripts/compute_features.py --audio data/raw_audio/demo.wav --events outputs/$$DATESTAMP/demo/events.csv --output outputs/$$DATESTAMP/demo/features.csv && \
	.venv/bin/python scripts/visualize.py --audio data/raw_audio/demo.wav --events outputs/$$DATESTAMP/demo/events.csv --features outputs/$$DATESTAMP/demo/features.csv --output-dir outputs/$$DATESTAMP/demo/viz && \
	.venv/bin/python scripts/build_report.py --events outputs/$$DATESTAMP/demo/events.csv --features outputs/$$DATESTAMP/demo/features.csv --meta outputs/$$DATESTAMP/demo/meta.json --viz-dir outputs/$$DATESTAMP/demo/viz --output outputs/$$DATESTAMP/demo/report.md && \
	echo "✓ MVP complete! Check outputs/$$DATESTAMP/demo/report.md"
endif

# Demo: Full pipeline with sample URL
demo: check-deps
	@echo "Running demo pipeline..."
ifeq ($(OS),Windows_NT)
	@echo https://www.youtube.com/watch?v=FRPeYP6gS-o > data\urls.txt
	@echo Sample URL written to data\urls.txt
	.venv\Scripts\python scripts\fetch_videos.py --url-file data\urls.txt --output data\raw_videos
	@for %%f in (data\raw_videos\*.mp4) do .venv\Scripts\python scripts\extract_audio.py --video %%f --output data\raw_audio\demo.wav --overwrite
	@$(MAKE) mvp
else
	@echo "https://www.youtube.com/watch?v=FRPeYP6gS-o" > data/urls.txt
	@echo "Sample URL written to data/urls.txt"
	.venv/bin/python scripts/fetch_videos.py --url-file data/urls.txt --output data/raw_videos
	@for video in data/raw_videos/*.mp4; do \
		.venv/bin/python scripts/extract_audio.py --video $$video --output data/raw_audio/demo.wav --overwrite; \
	done
	@$(MAKE) mvp
endif

# Testing
test:
ifeq ($(OS),Windows_NT)
	.venv\Scripts\pytest
else
	.venv/bin/pytest
endif

# Linting
lint:
ifeq ($(OS),Windows_NT)
	.venv\Scripts\flake8 thunder scripts tests
else
	.venv/bin/flake8 thunder scripts tests
endif

# Formatting
format:
ifeq ($(OS),Windows_NT)
	.venv\Scripts\black thunder scripts tests
else
	.venv/bin/black thunder scripts tests
endif

# Start Jupyter
notebooks:
ifeq ($(OS),Windows_NT)
	.venv\Scripts\jupyter lab notebooks
else
	.venv/bin/jupyter lab notebooks
endif

# Clean generated files
clean:
ifeq ($(OS),Windows_NT)
	@if exist build rmdir /s /q build
	@if exist dist rmdir /s /q dist
	@if exist *.egg-info rmdir /s /q *.egg-info
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist __pycache__ rmdir /s /q __pycache__
	@echo ✓ Cleaned build artifacts
else
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
	@echo "✓ Cleaned build artifacts"
endif
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf __pycache__ thunder/__pycache__ scripts/__pycache__
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Start Jupyter
notebooks:
	jupyter lab notebooks/
