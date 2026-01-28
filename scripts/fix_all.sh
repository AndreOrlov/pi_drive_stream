#!/bin/bash
# Автоматическое исправление проблем с кодом

# Активация виртуального окружения, если существует
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🔧 Auto-fixing code issues..."
echo ""

# 1. Ruff auto-fix
echo "📝 Step 1/2: Running ruff auto-fix..."
ruff check app/ tests/ --fix
echo "✓ Ruff auto-fix completed"
echo ""

# 2. Ruff formatter
echo "🎨 Step 2/2: Formatting code..."
ruff format app/ tests/
echo "✓ Code formatting completed"
echo ""

echo "✓ All auto-fixes applied!"
echo "Run './scripts/run_ci_checks.sh' to verify."
