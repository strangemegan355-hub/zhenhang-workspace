#!/usr/bin/env bash
# Local CI verification — run before pushing.
# Usage: bash scripts/ci.sh

set -e
cd "$(dirname "$0")/.."

echo "=== Backend: Python syntax check ==="
python -c "
import sys
from pathlib import Path
errors = []
for f in Path('backend').rglob('*.py'):
    if 'node_modules' in str(f) or '__pycache__' in str(f):
        continue
    try:
        compile(f.read_text(encoding='utf-8'), str(f), 'exec')
    except (SyntaxError, UnicodeDecodeError) as e:
        errors.append(f'{f}: {e}')
if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('OK')
"

echo ""
echo "=== Backend: pytest ==="
cd backend
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
cd ..

echo ""
echo "=== Frontend: ESLint ==="
npm run lint -w web-admin 2>&1 | tail -3

echo ""
echo "=== Frontend: Build ==="
npm run build -w web-admin 2>&1 | tail -5

echo ""
echo "=== All checks passed ==="
