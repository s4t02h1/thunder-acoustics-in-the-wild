# check_deps.ps1
# Check external dependencies (ffmpeg, yt-dlp) for Windows

$ErrorActionPreference = "Continue"

Write-Host "Checking external dependencies..." -ForegroundColor Cyan

# Check ffmpeg
$ffmpegFound = $false
try {
    $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ ffmpeg found: $ffmpegVersion" -ForegroundColor Green
        $ffmpegFound = $true
    }
} catch {
    # ffmpeg not found
}

if (-not $ffmpegFound) {
    Write-Host "✗ ERROR: ffmpeg not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install ffmpeg using one of these methods:" -ForegroundColor Yellow
    Write-Host "  1. Chocolatey: choco install ffmpeg" -ForegroundColor White
    Write-Host "  2. Scoop: scoop install ffmpeg" -ForegroundColor White
    Write-Host "  3. Manual: Download from https://ffmpeg.org/download.html" -ForegroundColor White
    Write-Host "     - Extract to C:\ffmpeg" -ForegroundColor White
    Write-Host "     - Add C:\ffmpeg\bin to PATH" -ForegroundColor White
    Write-Host ""
    
    # Append to README if not already present
    $readmePath = Join-Path $PSScriptRoot "..\..\README.md"
    if (Test-Path $readmePath) {
        $readmeContent = Get-Content $readmePath -Raw
        if ($readmeContent -notmatch "ffmpeg installation") {
            $installGuide = @"

---

## ⚠️ Missing Dependency: ffmpeg

**ffmpeg** is required for audio extraction. Install using:

### Windows
1. **Chocolatey** (recommended):
   ``````powershell
   choco install ffmpeg
   ``````

2. **Scoop**:
   ``````powershell
   scoop install ffmpeg
   ``````

3. **Manual**:
   - Download from https://ffmpeg.org/download.html
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to PATH environment variable

### macOS
``````bash
brew install ffmpeg
``````

### Linux (Ubuntu/Debian)
``````bash
sudo apt update
sudo apt install ffmpeg
``````

After installation, restart your terminal and run `make check-deps` again.
"@
            Add-Content -Path $readmePath -Value $installGuide
            Write-Host "Installation guide appended to README.md" -ForegroundColor Yellow
        }
    }
    
    exit 1
}

# Check yt-dlp
$ytdlpFound = $false
try {
    $ytdlpVersion = & yt-dlp --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ yt-dlp found: version $ytdlpVersion" -ForegroundColor Green
        $ytdlpFound = $true
    }
} catch {
    # yt-dlp not found
}

if (-not $ytdlpFound) {
    Write-Host "⚠ WARNING: yt-dlp not found in PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Attempting to install yt-dlp via pip..." -ForegroundColor Cyan
    
    # Try to install via pip
    try {
        $venvPython = Join-Path $PSScriptRoot "..\..\..\.venv\Scripts\python.exe"
        if (Test-Path $venvPython) {
            & $venvPython -m pip install yt-dlp --quiet
            
            # Check if successful
            $venvYtdlp = Join-Path $PSScriptRoot "..\..\..\.venv\Scripts\yt-dlp.exe"
            if (Test-Path $venvYtdlp) {
                $ytdlpVersion = & $venvYtdlp --version 2>&1
                Write-Host "✓ yt-dlp installed in venv: version $ytdlpVersion" -ForegroundColor Green
                
                # Add venv Scripts to PATH temporarily
                $venvScripts = Join-Path $PSScriptRoot "..\..\..\.venv\Scripts"
                if ($env:PATH -notlike "*$venvScripts*") {
                    $env:PATH = "$venvScripts;$env:PATH"
                    Write-Host "ℹ Added .venv\Scripts to PATH (current session only)" -ForegroundColor Cyan
                }
                
                $ytdlpFound = $true
            }
        }
    } catch {
        Write-Host "✗ Failed to install yt-dlp" -ForegroundColor Red
    }
}

if (-not $ytdlpFound) {
    Write-Host "✗ ERROR: yt-dlp not available" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install yt-dlp using one of these methods:" -ForegroundColor Yellow
    Write-Host "  1. pip: python -m pip install yt-dlp" -ForegroundColor White
    Write-Host "  2. Chocolatey: choco install yt-dlp" -ForegroundColor White
    Write-Host "  3. Scoop: scoop install yt-dlp" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "✓ All dependencies satisfied!" -ForegroundColor Green
exit 0
