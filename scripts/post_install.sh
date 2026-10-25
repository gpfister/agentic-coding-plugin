#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "==> Running post_install for gp-coding-plugin..."
cd "${PLUGIN_DIR}"

if ! command -v uv &> /dev/null; then
    echo "ERROR: 'uv' is not installed or not in PATH." >&2
    echo "Please install uv: brew install uv  OR  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

echo "==> Generating virtual environment via 'uv sync'..."
uv sync

echo "==> Post-install completed successfully. Virtual environment ready at: ${PLUGIN_DIR}/.venv"
