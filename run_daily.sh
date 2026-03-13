#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/a11681/Documents/OZ/My_Project/career_qa_v0.3 2"
PYTHON_BIN="$PROJECT_DIR/bin/python"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

"$PYTHON_BIN" main.py >> "$LOG_DIR/daily.log" 2>&1
