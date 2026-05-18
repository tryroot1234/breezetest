# BreezeTest One-Click Installer for Windows
# Usage: irm https://raw.githubusercontent.com/OWNER/breezetest/main/install.ps1 | iex
#   or:  .\install.ps1 [-Help] [-NoVenv] [-PythonPath PATH]

#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Help,
    [switch]$NoVenv,
    [switch]$SkipPlaywright,
    [string]$PythonPath = "",
    [string]$Version = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ScriptVersion = "1.0.0"
$MinPythonMajor = 3
$MinPythonMinor = 9
$VenvDir = ".breezetest-venv"

# Override from environment
if ($env:BREEZETEST_VENV_DIR) { $VenvDir = $env:BREEZETEST_VENV_DIR }
if ($env:BREEZETEST_VERSION -and -not $Version) { $Version = $env:BREEZETEST_VERSION }

# --- Logging ---
function Write-Log { param([string]$Msg) Write-Host "[breezetest] $Msg" }
function Write-Ok  { param([string]$Msg) Write-Host "[breezetest] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "[breezetest] ! $Msg" -ForegroundColor Yellow }
function Write-Err { param([string]$Msg) Write-Host "[breezetest] X $Msg" -ForegroundColor Red }
function Write-Step { param([string]$Msg) Write-Host "[breezetest] $Msg" -ForegroundColor Cyan }

# --- Usage ---
function Show-Usage {
    @"
BreezeTest Installer v$ScriptVersion

Usage: .\install.ps1 [OPTIONS]

Options:
  -Help               Show this help message
  -NoVenv             Skip virtual environment creation
  -PythonPath PATH    Use specific Python interpreter
  -Version VERSION    Install a specific version (default: latest)
  -DryRun             Show what would be done without executing

Environment Variables:
  BREEZETEST_VERSION  Install a specific version
  BREEZETEST_VENV_DIR Virtual environment directory (default: .breezetest-venv)

Examples:
  .\install.ps1                             # Default install with venv
  .\install.ps1 -NoVenv                     # Install into current environment
  .\install.ps1 -PythonPath C:\Python312\python.exe
  .\install.ps1 -Version 0.1.0             # Pin version
"@
}

# --- Find Python ---
function Find-Python {
    $candidates = @()
    if ($PythonPath) { $candidates += $PythonPath }
    $candidates += @("python3", "python", "py")

    foreach ($candidate in $candidates) {
        try {
            $ver = & $candidate -c "import sys; v=sys.version_info; print(f'{v.major}.{v.minor}') if (v.major,v.minor)>=($MinPythonMajor,$MinPythonMinor) else sys.exit(1)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $ver) {
                $fullVer = & $candidate --version 2>&1
                return @{
                    Command = $candidate
                    Version = $ver
                    FullVersion = $fullVer
                }
            }
        } catch { }
    }
    return $null
}

# --- Install Python ---
function Install-Python {
    Write-Step "Installing Python ${MinPythonMajor}.${MinPythonMinor}+..."

    if ($DryRun) {
        Write-Log "[dry-run] Would install Python"
        return
    }

    $installed = $false

    # Try winget
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Log "Using winget to install Python..."
        try {
            winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
            $installed = $true
        } catch {
            Write-Warn "winget install failed, trying Chocolatey..."
        }
    }

    # Try Chocolatey
    if (-not $installed -and (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Log "Using Chocolatey to install Python..."
        try {
            choco install python3 -y
            $installed = $true
        } catch {
            Write-Warn "Chocolatey install failed"
        }
    }

    if (-not $installed) {
        Write-Err "No supported package manager found (winget or Chocolatey)."
        Write-Err "Please install Python manually from: https://www.python.org/downloads/"
        Write-Err "After installation, restart PowerShell and run this script again."
        exit 1
    }

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Verify
    $python = Find-Python
    if ($python) {
        Write-Ok "Python $($python.FullVersion) installed"
    } else {
        Write-Err "Python installation could not be verified. Please restart PowerShell and try again."
        exit 1
    }
}

# --- Create venv ---
function New-BreezeVenv {
    Write-Step "Creating virtual environment in $VenvDir..."

    if ($DryRun) {
        Write-Log "[dry-run] Would create venv: python -m venv $VenvDir"
        return
    }

    if (Test-Path $VenvDir) {
        Write-Warn "Virtual environment already exists at $VenvDir"
        Write-Log "Using existing environment."
    } else {
        python -m venv $VenvDir
        Write-Ok "Virtual environment created"
    }

    # Activate
    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        # Check execution policy
        $policy = Get-ExecutionPolicy
        if ($policy -eq "Restricted") {
            Write-Warn "PowerShell execution policy is Restricted."
            Write-Log "Setting execution policy for current user..."
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        }
        . $activateScript
        Write-Ok "Virtual environment activated"
    } else {
        Write-Err "Activation script not found at $activateScript"
        exit 1
    }
}

# --- Install BreezeTest ---
function Install-BreezeTest {
    $pkg = "breezetest"
    if ($Version) { $pkg = "breezetest==$Version" }

    Write-Step "Installing BreezeTest..."

    if ($DryRun) {
        Write-Log "[dry-run] Would run: pip install $pkg"
        return
    }

    # Retry wrapper
    pip install --upgrade pip 2>$null

    # Try PyPI first, fall back to GitHub if not published yet
    try {
        pip install $pkg 2>$null
    } catch {
        Write-Warn "BreezeTest not found on PyPI, installing from GitHub..."
        $githubUrl = "https://github.com/tryroot1234/breezetest.git"
        if ($Version) { $githubUrl = "${githubUrl}@v$Version" }
        for ($i = 1; $i -le 3; $i++) {
            try {
                pip install "git+$githubUrl"
                break
            } catch {
                if ($i -eq 3) { throw }
                Write-Warn "Attempt $i/3 failed, retrying..."
                Start-Sleep -Seconds ($i * 2)
            }
        }
    }

    $breezeVer = & breeze --version 2>$null
    Write-Ok "BreezeTest $breezeVer installed"
}

# --- Install Playwright ---
function Install-PlaywrightBrowser {
    Write-Step "Installing Playwright Chromium browser..."

    if ($DryRun) {
        Write-Log "[dry-run] Would run: playwright install --with-deps chromium"
        return
    }

    for ($i = 1; $i -le 3; $i++) {
        try {
            playwright install --with-deps chromium
            break
        } catch {
            if ($i -eq 3) { throw }
            Write-Warn "Attempt $i/3 failed, retrying..."
            Start-Sleep -Seconds ($i * 2)
        }
    }

    Write-Ok "Playwright Chromium installed"
}

# --- Print success ---
function Show-Success {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "  BreezeTest installed successfully!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""

    if (-not $NoVenv) {
        Write-Host "  Virtual environment: $VenvDir" -ForegroundColor White
        Write-Host ""
        Write-Host "  To activate in new sessions:" -ForegroundColor White
        Write-Host "    .\$VenvDir\Scripts\Activate.ps1"
        Write-Host ""
    }

    Write-Host "  Get started:" -ForegroundColor White
    Write-Host "    breeze init --with-examples"
    Write-Host "    breeze run tests/"
    Write-Host ""
}

# --- Main ---
if ($Help) {
    Show-Usage
    exit 0
}

Write-Host "BreezeTest Installer v$ScriptVersion" -ForegroundColor Cyan
Write-Host ""

# Find or install Python
$python = Find-Python
if ($python) {
    Write-Ok "Python $($python.FullVersion) found: $($python.Command)"
} else {
    Install-Python
}

# Create venv
if (-not $NoVenv) {
    New-BreezeVenv
}

# Install BreezeTest
Install-BreezeTest

# Install Playwright
if ($SkipPlaywright) {
    Write-Warn "Skipping Playwright browser installation (-SkipPlaywright)"
    Write-Log "Run 'playwright install --with-deps chromium' later to install the browser."
} else {
    Install-PlaywrightBrowser
}

# Done
if (-not $DryRun) {
    Show-Success
} else {
    Write-Host ""
    Write-Log "[dry-run] Installation steps would be executed in the order shown above."
}
