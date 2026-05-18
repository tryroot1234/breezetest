# BreezeTest Developer Installer for Windows
# Sets up a full development environment with editable install and dev dependencies.

#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Help,
    [string]$PythonPath = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ScriptVersion = "1.0.0"
$MinPythonMajor = 3
$MinPythonMinor = 9
$RepoUrl = "https://github.com/tryroot1234/breezetest.git"
$VenvDir = ".venv"

# --- Logging ---
function Write-Log { param([string]$Msg) Write-Host "[breezetest] $Msg" }
function Write-Ok  { param([string]$Msg) Write-Host "[breezetest] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "[breezetest] ! $Msg" -ForegroundColor Yellow }
function Write-Err { param([string]$Msg) Write-Host "[breezetest] X $Msg" -ForegroundColor Red }
function Write-Step { param([string]$Msg) Write-Host "[breezetest] $Msg" -ForegroundColor Cyan }

# --- Usage ---
function Show-Usage {
    @"
BreezeTest Developer Installer v$ScriptVersion

Usage: .\install-dev.ps1 [OPTIONS]

Options:
  -Help               Show this help message
  -PythonPath PATH    Use specific Python interpreter
  -DryRun             Show what would be done without executing

This script:
  1. Clones the repository (or uses current directory if already in repo)
  2. Creates a virtual environment (.venv)
  3. Installs BreezeTest in editable mode with dev dependencies
  4. Installs Playwright Chromium browser

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

# --- Check if in repo ---
function Test-InRepo {
    return (Test-Path "pyproject.toml") -and (Select-String -Path "pyproject.toml" -Pattern "breezetest" -Quiet)
}

# --- Clone repo ---
function Copy-Repo {
    $targetDir = "breezetest"

    Write-Step "Cloning BreezeTest repository..."

    if ($DryRun) {
        Write-Log "[dry-run] Would clone $RepoUrl"
        return
    }

    if (Test-Path $targetDir) {
        Write-Warn "Directory '$targetDir' already exists"
        Set-Location $targetDir
        return
    }

    for ($i = 1; $i -le 3; $i++) {
        try {
            git clone $RepoUrl $targetDir
            break
        } catch {
            if ($i -eq 3) { throw }
            Write-Warn "Attempt $i/3 failed, retrying in $($i * 2)s..."
            Start-Sleep -Seconds ($i * 2)
        }
    }

    Set-Location $targetDir
    Write-Ok "Repository cloned"
}

# --- Create dev venv ---
function New-DevVenv {
    Write-Step "Creating development virtual environment..."

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
        $policy = Get-ExecutionPolicy
        if ($policy -eq "Restricted") {
            Write-Warn "PowerShell execution policy is Restricted."
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        }
        . $activateScript
        Write-Ok "Virtual environment activated"
    } else {
        Write-Err "Activation script not found at $activateScript"
        exit 1
    }
}

# --- Install dev dependencies ---
function Install-DevDeps {
    Write-Step "Installing BreezeTest in editable mode with dev dependencies..."

    if ($DryRun) {
        Write-Log "[dry-run] Would run: pip install -e '.[dev]'"
        return
    }

    for ($i = 1; $i -le 3; $i++) {
        try {
            pip install --upgrade pip 2>$null
            pip install -e ".[dev]"
            break
        } catch {
            if ($i -eq 3) { throw }
            Write-Warn "Attempt $i/3 failed, retrying..."
            Start-Sleep -Seconds ($i * 2)
        }
    }

    $breezeVer = & breeze --version 2>$null
    Write-Ok "BreezeTest $breezeVer installed (editable, with dev deps)"
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

# --- Setup pre-commit ---
function Initialize-PreCommit {
    if (Test-Path ".pre-commit-config.yaml") {
        Write-Step "Setting up pre-commit hooks..."
        if ($DryRun) {
            Write-Log "[dry-run] Would run: pre-commit install"
            return
        }
        pip install pre-commit
        pre-commit install
        Write-Ok "Pre-commit hooks installed"
    }
}

# --- Print dev instructions ---
function Show-DevInstructions {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "  Development environment ready!" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Activate the environment:" -ForegroundColor White
    Write-Host "    .\$VenvDir\Scripts\Activate.ps1"
    Write-Host ""
    Write-Host "  Run tests:" -ForegroundColor White
    Write-Host "    pytest tests/ -v"
    Write-Host ""
    Write-Host "  Lint & format:" -ForegroundColor White
    Write-Host "    ruff check src/ tests/"
    Write-Host "    ruff format src/ tests/"
    Write-Host ""
    Write-Host "  Type check:" -ForegroundColor White
    Write-Host "    mypy src/breezetest/"
    Write-Host ""
    Write-Host "  Run BreezeTest CLI:" -ForegroundColor White
    Write-Host "    breeze --help"
    Write-Host "    breeze run templates/example_test.yml"
    Write-Host ""
    Write-Host "  Build package:" -ForegroundColor White
    Write-Host "    pip install build; python -m build"
    Write-Host ""
}

# --- Main ---
if ($Help) {
    Show-Usage
    exit 0
}

Write-Host "BreezeTest Developer Installer v$ScriptVersion" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Find-Python
if (-not $python) {
    Write-Err "Python >= ${MinPythonMajor}.${MinPythonMinor} not found."
    Write-Err "Please install Python first: https://www.python.org/downloads/"
    exit 1
}
Write-Ok "Python $($python.FullVersion) found: $($python.Command)"

# Check if in repo or clone
if (Test-InRepo) {
    Write-Log "Already in BreezeTest repository directory"
} else {
    Copy-Repo
}

# Setup
New-DevVenv
Install-DevDeps
Install-PlaywrightBrowser
Initialize-PreCommit

if (-not $DryRun) {
    Show-DevInstructions
} else {
    Write-Host ""
    Write-Log "[dry-run] Installation steps would be executed in the order shown above."
}
