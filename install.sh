#!/usr/bin/env bash
set -euo pipefail

# BreezeTest One-Click Installer for macOS and Linux
# Usage: curl -sSL https://raw.githubusercontent.com/OWNER/breezetest/main/install.sh | bash
#   or:  bash install.sh [--help] [--no-venv] [--python PATH]

SCRIPT_VERSION="1.0.0"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=9
BREEZETEST_VERSION="${BREEZETEST_VERSION:-}"
VENV_DIR="${BREEZETEST_VENV_DIR:-.breezetest-venv}"

# --- Flags ---
NO_VENV=false
SKIP_PLAYWRIGHT=false
PYTHON_PATH=""
SHOW_HELP=false
DRY_RUN=false

# --- Colors ---
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' NC=''
fi

# --- Logging ---
log_info()  { echo -e "${CYAN}[breezetest]${NC} $*"; }
log_ok()    { echo -e "${CYAN}[breezetest]${NC} ${GREEN}✓${NC} $*"; }
log_warn()  { echo -e "${CYAN}[breezetest]${NC} ${YELLOW}!${NC} $*"; }
log_error() { echo -e "${CYAN}[breezetest]${NC} ${RED}✗${NC} $*" >&2; }
log_step()  { echo -e "${CYAN}[breezetest]${NC} ${BOLD}$*${NC}"; }

# --- Cleanup trap ---
CLEANUP_VENV=false
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]] && $CLEANUP_VENV; then
        if [[ -d "$VENV_DIR" ]]; then
            log_warn "Cleaning up partial installation..."
            rm -rf "$VENV_DIR"
        fi
    fi
}
trap cleanup EXIT

# --- Usage ---
usage() {
    cat <<EOF
BreezeTest Installer v${SCRIPT_VERSION}

Usage: install.sh [OPTIONS]

Options:
  --help, -h          Show this help message
  --no-venv           Skip virtual environment creation
  --skip-playwright   Skip Playwright browser installation
  --python PATH       Use specific Python interpreter
  --dry-run           Show what would be done without executing

Environment Variables:
  BREEZETEST_VERSION  Install a specific version (default: latest)
  BREEZETEST_VENV_DIR Virtual environment directory (default: .breezetest-venv)

Examples:
  bash install.sh                           # Default install with venv
  bash install.sh --no-venv                 # Install into current environment
  bash install.sh --python /usr/bin/python3.12
  BREEZETEST_VERSION=0.1.0 bash install.sh  # Pin version
EOF
}

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)          SHOW_HELP=true; shift ;;
        --no-venv)          NO_VENV=true; shift ;;
        --skip-playwright)  SKIP_PLAYWRIGHT=true; shift ;;
        --python)           PYTHON_PATH="$2"; shift 2 ;;
        --python=*)         PYTHON_PATH="${1#*=}"; shift ;;
        --dry-run)          DRY_RUN=true; shift ;;
        -*)                 log_error "Unknown option: $1"; usage; exit 1 ;;
        *)                  log_error "Unexpected argument: $1"; usage; exit 1 ;;
    esac
done

# --- OS Detection ---
detect_os() {
    OS="$(uname -s)"
    case "$OS" in
        Darwin) OS="macos" ;;
        Linux)  OS="linux" ;;
        *)
            log_error "Unsupported OS: $OS"
            log_error "This script supports macOS and Linux. For Windows, use install.ps1"
            exit 1
            ;;
    esac

    DISTRO=""
    if [[ "$OS" == "linux" ]] && [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO="${ID:-unknown}"
    fi
}

# --- Package manager detection ---
detect_pkg_mgr() {
    PKG_MGR=""
    if [[ "$OS" == "macos" ]]; then
        if command -v brew &>/dev/null; then
            PKG_MGR="brew"
        fi
    else
        for mgr in apt-get dnf pacman yum zypper; do
            if command -v "$mgr" &>/dev/null; then
                PKG_MGR="$mgr"
                break
            fi
        done
    fi
}

# --- Check if running as root ---
is_root() { [[ $EUID -eq 0 ]]; }

# --- Run with sudo if needed ---
run_privileged() {
    if is_root; then
        "$@"
    else
        sudo "$@"
    fi
}

# --- Retry wrapper ---
retry() {
    local max_attempts=3
    local delay=2
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if "$@"; then
            return 0
        fi
        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Attempt $attempt/$max_attempts failed, retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))
        fi
        ((attempt++))
    done

    log_error "Failed after $max_attempts attempts"
    return 1
}

# --- Python detection ---
find_python() {
    local candidates=()

    # User-specified path first
    if [[ -n "$PYTHON_PATH" ]]; then
        candidates+=("$PYTHON_PATH")
    fi

    # Standard names
    candidates+=(python3 python)

    for candidate in "${candidates[@]}"; do
        if [[ -x "$candidate" ]] || command -v "$candidate" &>/dev/null; then
            local version
            version=$("$candidate" -c "
import sys
v = sys.version_info
if (v.major, v.minor) >= ($MIN_PYTHON_MAJOR, $MIN_PYTHON_MINOR):
    print(f'{v.major}.{v.minor}.{v.micro}')
else:
    sys.exit(1)
" 2>/dev/null) && {
                PYTHON_CMD="$candidate"
                PYTHON_VERSION="$version"
                return 0
            }
        fi
    done

    return 1
}

# --- Install Python ---
install_python() {
    log_step "Installing Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+..."

    if $DRY_RUN; then
        log_info "[dry-run] Would install Python via $PKG_MGR"
        return 0
    fi

    case "$OS" in
        macos)
            if [[ -z "$PKG_MGR" ]]; then
                log_info "Homebrew not found. Installing Homebrew first..."
                retry /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
                PKG_MGR="brew"
            fi
            retry brew install python@3.12
            # Add to PATH for this session
            export PATH="$(brew --prefix)/opt/python@3.12/bin:$PATH"
            ;;
        linux)
            case "$PKG_MGR" in
                apt-get)
                    run_privileged apt-get update -qq
                    run_privileged apt-get install -y -qq python3 python3-pip python3-venv python3-dev
                    ;;
                dnf)
                    run_privileged dnf install -y python3 python3-pip python3-devel
                    ;;
                pacman)
                    run_privileged pacman -S --noconfirm python python-pip
                    ;;
                yum)
                    run_privileged yum install -y python3 python3-pip python3-devel
                    ;;
                zypper)
                    run_privileged zypper install -y python3 python3-pip python3-devel
                    ;;
                *)
                    log_error "No supported package manager found."
                    log_error "Please install Python >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} manually."
                    log_error "Download: https://www.python.org/downloads/"
                    exit 1
                    ;;
            esac
            ;;
    esac

    # Verify installation
    if find_python; then
        log_ok "Python $PYTHON_VERSION installed"
    else
        log_error "Python installation failed. Please install Python >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} manually."
        exit 1
    fi
}

# --- Create virtual environment ---
create_venv() {
    log_step "Creating virtual environment in $VENV_DIR..."

    if $DRY_RUN; then
        log_info "[dry-run] Would create venv: $PYTHON_CMD -m venv $VENV_DIR"
        return 0
    fi

    if [[ -d "$VENV_DIR" ]]; then
        log_warn "Virtual environment already exists at $VENV_DIR"
        log_info "Using existing environment."
    else
        CLEANUP_VENV=true
        "$PYTHON_CMD" -m venv "$VENV_DIR"
        CLEANUP_VENV=false
        log_ok "Virtual environment created"
    fi

    # Activate
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    log_ok "Virtual environment activated"
}

# --- Install BreezeTest ---
install_breezetest() {
    local pkg="breezetest"
    [[ -n "$BREEZETEST_VERSION" ]] && pkg="breezetest==$BREEZETEST_VERSION"

    log_step "Installing BreezeTest..."

    if $DRY_RUN; then
        log_info "[dry-run] Would run: pip install $pkg"
        return 0
    fi

    retry pip install --upgrade pip

    # Check if already installed
    local existing_version
    existing_version=$(breeze --version 2>/dev/null || true)

    # Try PyPI first, fall back to GitHub if not published yet
    if ! pip install --upgrade "$pkg" 2>/dev/null; then
        log_warn "BreezeTest not found on PyPI, installing from GitHub..."
        local github_url="https://github.com/tryroot1234/breezetest.git"
        if [[ -n "$BREEZETEST_VERSION" ]]; then
            github_url="${github_url}@v${BREEZETEST_VERSION}"
        fi
        if [[ -n "$existing_version" ]]; then
            log_info "Updating from $existing_version..."
            retry pip install --force-reinstall "git+${github_url}"
        else
            retry pip install "git+${github_url}"
        fi
    fi

    local installed_version
    installed_version=$(breeze --version 2>/dev/null || true)
    log_ok "BreezeTest $installed_version installed"
}

# --- Install Playwright ---
install_playwright() {
    log_step "Installing Playwright Chromium browser..."

    if $DRY_RUN; then
        log_info "[dry-run] Would run: playwright install --with-deps chromium"
        return 0
    fi

    retry playwright install --with-deps chromium
    log_ok "Playwright Chromium installed"
}

# --- Print success message ---
print_success() {
    echo ""
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  BreezeTest installed successfully!${NC}"
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
    echo ""

    if ! $NO_VENV; then
        echo -e "  ${BOLD}Virtual environment:${NC} $VENV_DIR"
        echo ""
        echo -e "  ${BOLD}To activate in new sessions:${NC}"
        echo -e "    source $VENV_DIR/bin/activate"
        echo ""
    fi

    echo -e "  ${BOLD}Get started:${NC}"
    echo -e "    breeze init --with-examples"
    echo -e "    breeze run tests/"
    echo ""
    echo -e "  ${BOLD}Verify installation:${NC}"
    echo -e "    bash scripts/verify-install.sh"
    echo ""
}

# --- Main ---
main() {
    if $SHOW_HELP; then
        usage
        exit 0
    fi

    echo -e "${BOLD}BreezeTest Installer${NC} v${SCRIPT_VERSION}"
    echo ""

    # Detect environment
    detect_os
    detect_pkg_mgr
    log_info "OS: $OS ${DISTRO:+($DISTRO)}"

    # Python
    if find_python; then
        log_ok "Python $PYTHON_VERSION found: $PYTHON_CMD"
    else
        install_python
    fi

    # Virtual environment
    if ! $NO_VENV; then
        create_venv
    fi

    # Install BreezeTest
    install_breezetest

    # Install Playwright
    if $SKIP_PLAYWRIGHT; then
        log_warn "Skipping Playwright browser installation (--skip-playwright)"
        log_info "Run 'playwright install --with-deps chromium' later to install the browser."
    else
        install_playwright
    fi

    # Done
    if ! $DRY_RUN; then
        print_success
    else
        echo ""
        log_info "[dry-run] Installation steps would be executed in the order shown above."
    fi
}

main
