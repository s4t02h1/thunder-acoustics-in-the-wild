# test_setup.ps1
# Quick test to verify installation

Write-Host "Thunder Acoustics - Setup Test" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found" -ForegroundColor Red
    exit 1
}

# Check venv
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\python.exe") {
    $venvPython = .venv\Scripts\python.exe --version 2>&1
    Write-Host "  ✓ Virtual environment exists: $venvPython" -ForegroundColor Green
} else {
    Write-Host "  ✗ Virtual environment not found. Run: make setup" -ForegroundColor Red
    exit 1
}

# Check thunder package
Write-Host "[3/5] Checking thunder package..." -ForegroundColor Yellow
.venv\Scripts\python.exe -c "import thunder; print(thunder.__version__)" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    $version = .venv\Scripts\python.exe -c "import thunder; print(thunder.__version__)" 2>&1
    Write-Host "  ✓ thunder package installed: version $version" -ForegroundColor Green
} else {
    Write-Host "  ✗ thunder package not installed. Run: make install" -ForegroundColor Red
    exit 1
}

# Check dependencies
Write-Host "[4/5] Checking Python dependencies..." -ForegroundColor Yellow
$deps = @("numpy", "scipy", "librosa", "pandas", "matplotlib", "pyyaml")
$missingDeps = @()

foreach ($dep in $deps) {
    .venv\Scripts\python.exe -c "import $dep" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $dep" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dep (missing)" -ForegroundColor Red
        $missingDeps += $dep
    }
}

if ($missingDeps.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing dependencies: $($missingDeps -join ', ')" -ForegroundColor Red
    Write-Host "Run: make install" -ForegroundColor Yellow
    exit 1
}

# Check external tools
Write-Host "[5/5] Checking external tools..." -ForegroundColor Yellow

# Check ffmpeg
$ffmpegFound = $false
try {
    ffmpeg -version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ ffmpeg" -ForegroundColor Green
        $ffmpegFound = $true
    }
} catch {}

if (-not $ffmpegFound) {
    Write-Host "  ⚠ ffmpeg (not found - required for audio extraction)" -ForegroundColor Yellow
}

# Check yt-dlp
$ytdlpFound = $false
try {
    yt-dlp --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ yt-dlp" -ForegroundColor Green
        $ytdlpFound = $true
    }
} catch {}

if (-not $ytdlpFound) {
    # Check in venv
    if (Test-Path ".venv\Scripts\yt-dlp.exe") {
        Write-Host "  ✓ yt-dlp (in venv)" -ForegroundColor Green
        $ytdlpFound = $true
    } else {
        Write-Host "  ⚠ yt-dlp (not found - required for video download)" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "===============================" -ForegroundColor Cyan
if ($ffmpegFound -and $ytdlpFound) {
    Write-Host "✓ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready to run:" -ForegroundColor Cyan
    Write-Host "  make demo       # Full pipeline demo" -ForegroundColor White
    Write-Host "  jupyter lab notebooks/00_quickstart.ipynb" -ForegroundColor White
} else {
    Write-Host "⚠ Setup incomplete" -ForegroundColor Yellow
    Write-Host ""
    if (-not $ffmpegFound) {
        Write-Host "Install ffmpeg: choco install ffmpeg" -ForegroundColor Yellow
    }
    if (-not $ytdlpFound) {
        Write-Host "Install yt-dlp: .venv\Scripts\pip install yt-dlp" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Or run: make check-deps" -ForegroundColor Cyan
}
