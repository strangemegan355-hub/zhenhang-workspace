# Non-blocking backend ruff/mypy report (K-007). Always exits 0 unless -Strict.
param(
    [switch]$Strict,
    [switch]$SkipMypy
)
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$py = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$baseline = Join-Path $root "logs\ruff-backend-baseline.txt"
$args = @("scripts\check_backend_lint.py", "--baseline-out", $baseline)
if ($Strict) { $args += "--strict" }
if ($SkipMypy) { $args += "--skip-mypy" }
Push-Location $backend
try {
    & $py @args
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
if ($Strict) { exit $code } else { exit 0 }
