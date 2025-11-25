#!/bin/bash
# Локальный запуск всех CI проверок

set -e  # Остановка при первой ошибке

echo "🔍 Running CI checks locally..."
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Счётчик ошибок
ERRORS=0

# 1. Ruff linter
echo "📝 Step 1/4: Running ruff linter..."
if ruff check app/ tests/; then
    echo -e "${GREEN}✓ Ruff check passed${NC}"
else
    echo -e "${RED}✗ Ruff check failed${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. Ruff formatter
echo "🎨 Step 2/4: Checking code formatting..."
if ruff format --check app/ tests/; then
    echo -e "${GREEN}✓ Code formatting check passed${NC}"
else
    echo -e "${RED}✗ Code formatting check failed${NC}"
    echo -e "${YELLOW}Run 'ruff format app/ tests/' to fix${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. Mypy type checker
echo "🔎 Step 3/4: Running mypy type checker..."
if mypy app/ --ignore-missing-imports --no-error-summary; then
    echo -e "${GREEN}✓ Type check passed${NC}"
else
    echo -e "${YELLOW}⚠ Type check has warnings (non-blocking)${NC}"
    # Не увеличиваем ERRORS, т.к. в CI это continue-on-error: true
fi
echo ""

# 4. Pytest
echo "🧪 Step 4/4: Running tests..."
if pytest tests/ -v --cov=app/overlay --cov-report=term-missing; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Итоги
echo "================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All CI checks passed!${NC}"
    echo "You can safely push your code."
    exit 0
else
    echo -e "${RED}✗ $ERRORS check(s) failed${NC}"
    echo "Please fix the errors before pushing."
    exit 1
fi
