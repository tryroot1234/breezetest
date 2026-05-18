#!/usr/bin/env bash
set -euo pipefail

# BreezeTest Developer Installer for macOS and Linux
# Sets up a full development environment with editable install and dev dependencies.

SCRIPT_VERSION="1.0.0"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=9
REPO_URL="https://github.com/breezetest/breezetest.git"
VENV_DIR=".venv"

# --- Flags ---
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
BreezeTest Developer Installer v${SCRIPT_VERSION}

Usage: install-dev.sh [OPTIONS]

Options:
  --help, -h          Show this help message
  --python PATH       Use specific Python interpreter
  --dry-run           Show what would be done without executing

This script:
  1. Clones the repository (or uses current directory if already in repo)
  2. Creates a virtual environment (.venv)
  3. Installs BreezeTest in editable mode with dev dependencies
  4. Installs Playwright Chromium browser

EOF
}

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)     SHOW_HELP=true; shift ;;
        --python)      PYTHON_PATH="$2"; shift 2 ;;
        --python=*)    PYTHON_PATH="${1#*=}"; shift ;;
        --dry-run)     DRY_RUN=true; shift ;;
        -*)            log_error "Unknown option: $1"; usage; exit 1 ;;
        *)             log_error "Unexpected argument: $1"; usage; exit 1 ;;
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
            log_error "For Windows, use install-dev.ps1"
            exit 1
            ;;
    esac
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
    if [[ -n "$PYTHON_PATH" ]]; then
        candidates+=("$PYTHON_PATH")
    fi
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

# --- Detect if in repo ---
is_in_repo() {
    [[ -f "pyproject.toml" ]] && grep -q "breezetest" pyproject.toml 2>/dev/null
}

# --- Clone repo ---
clone_repo() {
    local target_dir="breezetest"

    log_step "Cloning BreezeTest repository..."

    if $DRY_RUN; then
        log_info "[dry-run] Would clone $REPO_URL"
        return 0
    fi

    if [[ -d "$target_dir" ]]; then
        log_warn "Directory '$target_dir' already exists"
        cd "$target_dir"
        return 0
    fi

    retry git clone "$REPO_URL" "$target_dir"
    cd "$target_dir"
    log_ok "Repository cloned"
}

# --- Create dev venv ---
create_dev_venv() {
    log_step "Creating development virtual environment..."

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

# --- Install dev dependencies ---
install_dev_deps() {
    log_step "Installing BreezeTest in editable mode with dev dependencies..."

    if $DRY_RUN; then
        log_info "[dry-run] Would run: pip install -e '.[dev]'"
        return 0
    fi

    retry pip install --upgrade pip
    retry pip install -e ".[dev]"

    local installed_version
    installed_version=$(breeze --version 2>/dev/null || true)
    log_ok "BreezeTest $installed_version installed (editable, with dev deps)"
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

# --- Setup pre-commit ---
setup_pre_commit() {
    if [[ -f ".pre-commit-config.yaml" ]]; then
        log_step "Setting up pre-commit hooks..."
        if $DRY_RUN; then
            log_info "[dry-run] Would run: pre-commit install"
            return 0
        fi
        pip install pre-commit
        pre-commit install
        log_ok "Pre-commit hooks installed"
    fi
}

# --- Print dev instructions ---
print_dev_instructions() {
    echo ""
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  Development environment ready!${NC}"
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BOLD}Activate the environment:${NC}"
    echo -e "    source $VENV_DIR/bin/activate"
    echo ""
    echo -e "  ${BOLD}Run tests:${NC}"
    echo -e "    pytest tests/ -v"
    echo ""
    echo -e "  ${BOLD}Lint & format:${NC}"
    echo -e "    ruff check src/ tests/"
    echo -e "    ruff format src/ tests/"
    echo ""
    echo -e "  ${BOLD}Type check:${NC}"
    echo -e "    mypy src/breezetest/"
    echo ""
    echo -e "  ${BOLD}Run BreezeTest CLI:${NC}"
    echo -e "    breeze --help"
    echo -e "    breeze run templates/example_test.yml"
    echo ""
    echo -e "  ${BOLD}Build package:${NC}"
    echo -e "    pip install build && python -m build"
    echo ""
}

# --- Main ---
main() {
    if $SHOW_HELP; then
        usage
        exit 0
    fi

    echo -e "${BOLD}BreezeTest Developer Installer${NC} v${SCRIPT_VERSION}"
    echo ""

    detect_os

    # Check Python
    if ! find_python; then
        log_error "Python >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} not found."
        log_error "Please install Python first, then re-run this script."
        log_error "Download: https://www.python.org/downloads/"
        exit 1
    fi
    log_ok "Python $PYTHON_VERSION found: $PYTHON_CMD"

    # Check if in repo or clone
    if is_in_repo; then
        log_info "Already in BreezeTest repository directory"
    else
        clone_repo
    fi

    # Setup
    create_dev_venv
    install_dev_deps
    install_playwright
    setup_pre_commit

    if ! $DRY_RUN; then
        print_dev_instructions
    else
        echo ""
        log_info "[dry-run] Installation steps would be executed in the order shown above."
    fi
}

main
