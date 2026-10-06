#!/usr/bin/env bash
# Local CI verification — run before pushing.
# Usage: bash scripts/ci.sh
#
# What this covers: the Python syntax check, the unit test suite in backend/tests, ESLint for web-admin, the
# web-admin production build, and the same four TypeScript checks .github/workflows/ci.yml runs (web-admin,
# tsconfig.packages.json, workshop-terminal, mobile-app).
# What it does NOT cover: the integration suite in backend/integration_tests (19 tests). Those need real
# PostgreSQL, Redis and MinIO, so they are not part of this script and running it before a push does not run
# them - .github/workflows/ci.yml does, and the README's "集成测试" section gives the command to run them
# locally.

set -e
# Without pipefail, `set -e` looks at the last command of a pipeline. Every check below ends in `| tail`,
# so a failing test, lint or build would be reported as "All checks passed".
set -o pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "=== Backend: Python syntax check ==="
python -c "
import sys
from pathlib import Path
errors = []
for f in Path('backend').rglob('*.py'):
    # .venv/site-packages: the virtualenv is not the project, and compiling it buries this
    # check in third-party SyntaxWarnings (passlib ships some).
    if any(part in str(f) for part in ('node_modules', '__pycache__', '.venv', 'site-packages')):
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
echo "=== Frontend: Type checks ==="
"$ROOT/node_modules/.bin/tsc" -p apps/web-admin/tsconfig.json --noEmit 2>&1 | tail -3
"$ROOT/node_modules/.bin/tsc" -p tsconfig.packages.json 2>&1 | tail -3
"$ROOT/node_modules/.bin/tsc" -p apps/workshop-terminal/tsconfig.json --noEmit 2>&1 | tail -3
"$ROOT/node_modules/.bin/tsc" -p apps/mobile-app/tsconfig.json --noEmit 2>&1 | tail -3

echo ""
echo "=== Frontend: Build ==="
npm run build -w web-admin 2>&1 | tail -5

echo ""
echo "=== All checks passed ==="
