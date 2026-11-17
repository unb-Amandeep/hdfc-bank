#!/bin/bash
# Convenience runner for HDFC Predictor
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="$BASE_DIR/.venv/bin/python"

if [ ! -f "$PYTHON_EXEC" ]; then
    echo "Virtual environment not found at $PYTHON_EXEC"
    exit 1
fi

"$PYTHON_EXEC" -m hdfc_predictor "$@"
