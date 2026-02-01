#!/bin/bash
# NHI CLI Installer
# Creates symlink for 'nhi' command

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_SCRIPT="$SCRIPT_DIR/cli/nhi.py"
SYMLINK_PATH="/usr/local/bin/nhi"

echo "Installing NHI CLI..."

# Make CLI executable
chmod +x "$CLI_SCRIPT"

# Create symlink
if [ -L "$SYMLINK_PATH" ]; then
    echo "Removing existing symlink..."
    sudo rm "$SYMLINK_PATH"
fi

sudo ln -s "$CLI_SCRIPT" "$SYMLINK_PATH"

echo "✅ NHI CLI installed successfully!"
echo "   Run 'nhi --help' to get started"
