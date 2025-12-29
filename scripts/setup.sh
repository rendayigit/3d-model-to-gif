#!/bin/bash
# =============================================================================
# Model Preview Generator - Setup Script
# =============================================================================
# This script sets up the development environment for the project.
# 
# Usage:
#   ./scripts/setup.sh
#
# =============================================================================

set -e

echo "=========================================="
echo "  Model Preview Generator Setup"
echo "=========================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Python 3.10 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi
echo -e "${GREEN}OK${NC} (Python $PYTHON_VERSION)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -n "Creating virtual environment... "
    python3 -m venv .venv
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -n "Activating virtual environment... "
source .venv/bin/activate
echo -e "${GREEN}OK${NC}"

# Upgrade pip
echo -n "Upgrading pip... "
pip install --upgrade pip -q
echo -e "${GREEN}OK${NC}"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo -n "Installing development dependencies... "
pip install -e ".[dev]" -q 2>/dev/null || pip install pytest black ruff mypy -q
echo -e "${GREEN}OK${NC}"

# Check for Linux-specific dependencies
if [ "$(uname)" == "Linux" ]; then
    echo
    echo -e "${YELLOW}Linux detected - checking system dependencies...${NC}"
    
    # Check for libxcb-cursor
    if ! ldconfig -p | grep -q libxcb-cursor; then
        echo -e "${YELLOW}Warning: libxcb-cursor not found${NC}"
        echo "The Qt GUI may not work without this library."
        echo
        echo "Install it with:"
        echo "  Ubuntu/Debian: sudo apt-get install libxcb-cursor0"
        echo "  Fedora:        sudo dnf install xcb-util-cursor"
        echo "  Arch:          sudo pacman -S xcb-util-cursor"
    else
        echo -e "  libxcb-cursor: ${GREEN}OK${NC}"
    fi
fi

echo
echo "=========================================="
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo
echo "To run the application:"
echo "  python main.py"
echo
