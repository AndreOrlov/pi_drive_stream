#!/bin/bash
# Pi Drive Stream - Quick start script
# Usage: ./start.sh

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Pi Drive Stream..."
echo "📁 Working directory: $SCRIPT_DIR"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Error: Virtual environment not found at .venv/"
    echo "💡 Run: python3 -m venv .venv --system-site-packages"
    exit 1
fi

# Check if pigpiod is running (for Raspberry Pi)
if command -v pgrep &> /dev/null && command -v pigpiod &> /dev/null; then
    if ! pgrep -x pigpiod > /dev/null; then
        echo "⚠️  Warning: pigpiod daemon is not running"
        echo "💡 Servo control will not work. Start with: sudo pigpiod"
    fi
fi

# Start server
echo "▶️  Starting server..."
python main.py

