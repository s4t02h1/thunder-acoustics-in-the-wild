#!/bin/bash
# check_deps.sh
# Check external dependencies (ffmpeg, yt-dlp) for Unix/macOS

set +e  # Don't exit on error

echo -e "\033[0;36mChecking external dependencies...\033[0m"

# Check ffmpeg
ffmpeg_found=false
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n1)
    echo -e "\033[0;32m✓ ffmpeg found: $ffmpeg_version\033[0m"
    ffmpeg_found=true
else
    echo -e "\033[0;31m✗ ERROR: ffmpeg not found\033[0m"
    echo ""
    echo -e "\033[0;33mInstall ffmpeg using one of these methods:\033[0m"
    echo -e "  macOS: brew install ffmpeg"
    echo -e "  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
    echo -e "  Fedora: sudo dnf install ffmpeg"
    echo ""
    
    # Append to README if not already present
    readme_path="README.md"
    if [ -f "$readme_path" ]; then
        if ! grep -q "ffmpeg installation" "$readme_path"; then
            cat >> "$readme_path" << 'EOF'

---

## ⚠️ Missing Dependency: ffmpeg

**ffmpeg** is required for audio extraction. Install using:

### macOS
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

### Windows
```powershell
choco install ffmpeg
```

After installation, restart your terminal and run `make check-deps` again.
EOF
            echo -e "\033[0;33mInstallation guide appended to README.md\033[0m"
        fi
    fi
    
    exit 1
fi

# Check yt-dlp
ytdlp_found=false
if command -v yt-dlp &> /dev/null; then
    ytdlp_version=$(yt-dlp --version 2>&1)
    echo -e "\033[0;32m✓ yt-dlp found: version $ytdlp_version\033[0m"
    ytdlp_found=true
else
    echo -e "\033[0;33m⚠ WARNING: yt-dlp not found in PATH\033[0m"
    echo ""
    echo -e "\033[0;36mAttempting to install yt-dlp via pip...\033[0m"
    
    # Try to install via pip in venv
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python -m pip install yt-dlp --quiet
        
        if [ -f ".venv/bin/yt-dlp" ]; then
            ytdlp_version=$(.venv/bin/yt-dlp --version 2>&1)
            echo -e "\033[0;32m✓ yt-dlp installed in venv: version $ytdlp_version\033[0m"
            
            # Add venv bin to PATH temporarily
            export PATH=".venv/bin:$PATH"
            echo -e "\033[0;36mℹ Added .venv/bin to PATH (current session only)\033[0m"
            ytdlp_found=true
        fi
    fi
fi

if [ "$ytdlp_found" = false ]; then
    echo -e "\033[0;31m✗ ERROR: yt-dlp not available\033[0m"
    echo ""
    echo -e "\033[0;33mInstall yt-dlp using one of these methods:\033[0m"
    echo -e "  pip: python -m pip install yt-dlp"
    echo -e "  macOS: brew install yt-dlp"
    echo -e "  Ubuntu: sudo apt install yt-dlp"
    echo ""
    exit 1
fi

echo ""
echo -e "\033[0;32m✓ All dependencies satisfied!\033[0m"
exit 0
