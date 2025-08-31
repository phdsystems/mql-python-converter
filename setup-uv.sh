#!/bin/bash

# Setup script for uv-based Python environment

set -e

echo "==================================="
echo "MQL-Python Converter Setup with uv"
echo "==================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Show uv version
echo "Using uv version: $(uv --version)"

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
uv venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install base dependencies
echo "Installing base dependencies..."
uv pip install -e .

# Ask about optimization libraries
read -p "Install optimization libraries? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing optimization libraries..."
    uv pip install -e ".[optimization]"
fi

# Show installed packages
echo ""
echo "Installed packages:"
uv pip list

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  python -m pytest"
echo ""
echo "To start the MT4 server:"
echo "  python server/mt4_server.py"