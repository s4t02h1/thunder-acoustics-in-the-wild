# set_permissions.ps1
# Set execute permissions for Unix scripts (when editing on Windows)

$unixScripts = @(
    "scripts\unix\check_deps.sh",
    "scripts\unix\batch_extract.py"
)

Write-Host "Setting executable permissions for Unix scripts..." -ForegroundColor Cyan

foreach ($script in $unixScripts) {
    if (Test-Path $script) {
        # Git will preserve +x when committed
        git update-index --chmod=+x $script 2>$null
        Write-Host "  ✓ $script" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $script (not found)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Note: Permissions will be applied on Unix/macOS after git clone" -ForegroundColor Cyan
