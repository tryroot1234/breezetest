#!/usr/bin/env bash
set -euo pipefail

# BreezeTest Installation Verification Script
# Checks that all components are correctly installed.

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASS=0
FAIL=0

pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASS++))
}

fail() {
    echo -e "  ${RED}✗${NC} $1"
    [[ -n "${2:-}" ]] && echo -e "    ${YELLOW}Fix:${NC} $2"
    ((FAIL++))
}

echo "BreezeTest Installation Verification"
echo "====================================="
echo ""

# 1. Check Python version
echo "Python:"
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        if [[ -n "$version" ]]; then
            major=${version%%.*}
            minor=${version##*.}
            if [[ "$major" -ge 3 ]] && [[ "$minor" -ge 9 ]]; then
                full_version=$("$candidate" --version 2>&1)
                pass "$full_version"
                PYTHON="$candidate"
                break
            fi
        fi
    fi
done
if [[ -z "$PYTHON" ]]; then
    fail "Python >= 3.9 not found" "Install Python 3.9+ from https://www.python.org/downloads/"
fi

# 2. Check pip
echo "pip:"
if command -v pip &>/dev/null || command -v pip3 &>/dev/null; then
    pip_version=$(pip --version 2>/dev/null || pip3 --version 2>/dev/null || true)
    if [[ -n "$pip_version" ]]; then
        pass "$pip_version"
    else
        fail "pip not working" "Run: python3 -m ensurepip --upgrade"
    fi
else
    fail "pip not found" "Run: python3 -m ensurepip --upgrade"
fi

# 3. Check breeze command
echo "BreezeTest CLI:"
if command -v breeze &>/dev/null; then
    breeze_version=$(breeze --version 2>/dev/null || true)
    if [[ -n "$breeze_version" ]]; then
        pass "breeze $breeze_version"
    else
        fail "breeze command exists but returned an error" "Try reinstalling: pip install --force-reinstall breezetest"
    fi
else
    fail "breeze command not found" "Run: pip install breezetest"
fi

# 4. Check Playwright browsers
echo "Playwright Chromium:"
if [[ -n "$PYTHON" ]]; then
    if "$PYTHON" -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()
" &>/dev/null; then
        pass "Chromium browser installed and launchable"
    else
        fail "Chromium browser not available" "Run: playwright install --with-deps chromium"
    fi
else
    fail "Skipped (Python not available)"
fi

# Summary
echo ""
echo "====================================="
echo -e "Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"

if [[ "$FAIL" -gt 0 ]]; then
    echo -e "${YELLOW}Some checks failed. See above for fix instructions.${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed! BreezeTest is ready to use.${NC}"
    echo ""
    echo "Get started:"
    echo "  breeze init --with-examples"
    echo "  breeze run tests/"
    exit 0
fi
