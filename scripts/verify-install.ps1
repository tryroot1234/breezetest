# BreezeTest Installation Verification Script (PowerShell)
# Checks that all components are correctly installed.

$ErrorActionPreference = "Continue"

$script:Pass = 0
$script:Fail = 0

function Write-Pass {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
    $script:Pass++
}

function Write-Fail {
    param([string]$Message, [string]$Fix = "")
    Write-Host "  [FAIL] $Message" -ForegroundColor Red
    if ($Fix) { Write-Host "    Fix: $Fix" -ForegroundColor Yellow }
    $script:Fail++
}

Write-Host "BreezeTest Installation Verification" -ForegroundColor Cyan
Write-Host "====================================="
Write-Host ""

# 1. Check Python version
Write-Host "Python:"
$pythonCmd = $null
foreach ($candidate in @("python3", "python", "py")) {
    try {
        $ver = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver) {
            $parts = $ver.Split(".")
            if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 9) {
                $fullVer = & $candidate --version 2>&1
                Write-Pass $fullVer
                $pythonCmd = $candidate
                break
            }
        }
    } catch { }
}
if (-not $pythonCmd) {
    Write-Fail "Python >= 3.9 not found" "Install from https://www.python.org/downloads/"
}

# 2. Check pip
Write-Host "pip:"
try {
    $pipVer = & pip --version 2>&1
    if ($pipVer -match "pip") {
        Write-Pass $pipVer
    } else {
        Write-Fail "pip not working" "Run: python -m ensurepip --upgrade"
    }
} catch {
    Write-Fail "pip not found" "Run: python -m ensurepip --upgrade"
}

# 3. Check breeze command
Write-Host "BreezeTest CLI:"
try {
    $breezeVer = & breeze --version 2>&1
    if ($breezeVer) {
        Write-Pass "breeze $breezeVer"
    } else {
        Write-Fail "breeze command returned an error" "Try: pip install --force-reinstall breezetest"
    }
} catch {
    Write-Fail "breeze command not found" "Run: pip install breezetest"
}

# 4. Check Playwright browsers
Write-Host "Playwright Chromium:"
if ($pythonCmd) {
    try {
        & $pythonCmd -c @"
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()
"@ 2>$null
        Write-Pass "Chromium browser installed and launchable"
    } catch {
        Write-Fail "Chromium browser not available" "Run: playwright install --with-deps chromium"
    }
} else {
    Write-Fail "Skipped (Python not available)"
}

# Summary
Write-Host ""
Write-Host "====================================="
Write-Host "Results: $($script:Pass) passed, $($script:Fail) failed"

if ($script:Fail -gt 0) {
    Write-Host "Some checks failed. See above for fix instructions." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "All checks passed! BreezeTest is ready to use." -ForegroundColor Green
    Write-Host ""
    Write-Host "Get started:"
    Write-Host "  breeze init --with-examples"
    Write-Host "  breeze run tests/"
    exit 0
}
