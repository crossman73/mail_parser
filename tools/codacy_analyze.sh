#!/bin/bash
# Codacy CLI v2 runner script for WSL
# Usage: ./codacy_analyze.sh [file_or_directory] [--tool tool_name]

cd /mnt/c/dev/python-email || exit 1

# Activate virtual environment if exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Run codacy-cli with all passed arguments
echo "Running Codacy CLI v2 analysis..."
bash <(curl -Ls https://raw.githubusercontent.com/codacy/codacy-cli-v2/main/codacy-cli.sh) analyze "$@"

echo ""
echo "Analysis complete."
