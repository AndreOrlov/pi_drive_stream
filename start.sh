#!/bin/bash
# Pi Drive Stream - Universal start script
# Works on both Desktop and Raspberry Pi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Pi Drive Stream..."

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment (venv)..."
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found"
    echo ""
    echo "📦 Setup instructions:"
    echo ""
    echo "Desktop (macOS/Linux/Windows):"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements-desktop.txt"
    echo ""
    echo "Raspberry Pi:"
    echo "  python3 -m venv --system-site-packages .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements-pi.txt"
    exit 1
fi

# Check if pigpiod is running (Raspberry Pi only)
if command -v pgrep &> /dev/null && command -v pigpiod &> /dev/null; then
    if ! pgrep -x pigpiod > /dev/null; then
        echo "⚠️  Warning: pigpiod daemon is not running"
        echo "💡 Servo control will not work. Start with: sudo systemctl start pigpiod"
    fi
fi

# Start server
echo "▶️  Starting server..."
python main.py
