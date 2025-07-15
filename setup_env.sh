#!/bin/bash

# Setup script for pandas_tutor development environment using uv

echo "Setting up pandas_tutor development environment with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null
then
    echo "uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies (creates venv automatically and installs dependencies)
echo "Syncing dependencies..."
uv sync --extra dev

echo "Setup complete! Activate the environment with:"
echo "source .venv/bin/activate"
