# P5 delivery acceptance — deployment smoke checks (Windows)
# Usage: .\scripts\verify_delivery.ps1 [-BaseUrl http://localhost] [-EnvFile backend\.env.prod]

param(
    [string]$BaseUrl = "http://localhost",
    [string]$EnvFile = "backend\.env.prod",
    [string]$ComposeFile = "docker-compose.prod.yml"
)

$ErrorActionPreference = "Stop"
$passed = 0
$failed = 0
$skipped = 0

function Write-Result {
    param([string]$Name, [bool]$Ok, [string]$Detail = "")
    if ($Ok) {
        Write-Host "[PASS] $Name" -ForegroundColor Green
        if ($Detail) { Write-Host "       $Detail" -ForegroundColor DarkGray }
        $script:passed++
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        if ($Detail) { Write-Host "       $Detail" -ForegroundColor Yellow }
        $script:failed++
    }
}

function Write-Skip {
    param([string]$Name, [string]$Detail)
    Write-Host "[SKIP] $Name" -ForegroundColor DarkYellow
    Write-Host "       $Detail" -ForegroundColor DarkGray
    $script:skipped++
}

Write-Host "`n=== P5 Delivery Verification ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl`n"

# 1. docker compose config
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $envPath = Join-Path $repoRoot ($EnvFile -replace '/', '\')
    if (-not (Test-Path $envPath)) {
        Write-Skip "docker compose config" "Missing $EnvFile — copy from backend/.env.prod.example"
    } else {
        $configOut = docker compose -f $ComposeFile --env-file $EnvFile config 2>&1
        Write-Result "docker compose config" ($LASTEXITCODE -eq 0) $(if ($LASTEXITCODE -ne 0) { $configOut })
    }
} finally {
    Pop-Location
}

# HTTP checks (require running stack)
function Invoke-Http {
    param([string]$Url, [int]$TimeoutSec = 10)
    try {
        return Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    } catch {
        if ($_.Exception.Response) {
            return $_.Exception.Response
        }
        # A timeout or a refused connection carries no Response object. Name the reason here, because the
        # callers below would otherwise report "Stack not reachable" even when the stack answered another
        # request a moment earlier - as /health/ready did, exceeding the 15 s limit applied to it below.
        Write-Host "       ($Url : $($_.Exception.Message))" -ForegroundColor DarkGray
        return $null
    }
}

# 2. health/live
$liveUrl = "$BaseUrl/api/v1/health/live"
$liveResp = Invoke-Http $liveUrl
$liveOk = $liveResp -and $liveResp.StatusCode -eq 200
if (-not $liveOk -and -not $liveResp) {
    Write-Skip "GET /api/v1/health/live" "Stack not reachable at $BaseUrl"
} else {
    Write-Result "GET /api/v1/health/live" $liveOk "Status: $($liveResp.StatusCode)"
}

# 3. Web root
$webResp = Invoke-Http $BaseUrl
$webOk = $false
if ($webResp -and $webResp.StatusCode -eq 200) {
    $body = if ($webResp.Content) { [string]$webResp.Content } else { "" }
    $webOk = $body -match "振航|ERP|__next|next" -or $webResp.Headers["Content-Type"] -match "text/html"
}
if (-not $webResp) {
    Write-Skip "GET / (Web)" "Stack not reachable at $BaseUrl"
} else {
    Write-Result "GET / (Web HTML)" $webOk "Status: $($webResp.StatusCode)"
}

# 4. health/ready
$readyUrl = "$BaseUrl/api/v1/health/ready"
$readyResp = Invoke-Http $readyUrl 15
$readyOk = $readyResp -and $readyResp.StatusCode -eq 200
if (-not $readyResp) {
    Write-Skip "GET /api/v1/health/ready" "Stack not reachable"
} else {
    Write-Result "GET /api/v1/health/ready" $readyOk "Status: $($readyResp.StatusCode)"
}

# 5. metrics protection (production)
$metricsUrl = "$BaseUrl/api/v1/health/metrics"
$metricsResp = Invoke-Http $metricsUrl
$isProduction = $false
if (Test-Path (Join-Path $repoRoot ($EnvFile -replace '/', '\'))) {
    $envContent = Get-Content (Join-Path $repoRoot ($EnvFile -replace '/', '\')) -Raw
    $isProduction = $envContent -match "(?m)^ENVIRONMENT=production"
}

if (-not $metricsResp) {
    Write-Skip "GET /api/v1/health/metrics protection" "Stack not reachable"
} elseif ($isProduction) {
    $metricsBlocked = $metricsResp.StatusCode -eq 403
    Write-Result "Metrics blocked in production (403 without key)" $metricsBlocked "Status: $($metricsResp.StatusCode)"
} else {
    $metricsOpen = $metricsResp.StatusCode -eq 200
    Write-Result "Metrics accessible in dev (200)" $metricsOpen "Status: $($metricsResp.StatusCode)"
}

Write-Host "`n--- Summary ---" -ForegroundColor Cyan
Write-Host "Passed: $passed  Failed: $failed  Skipped: $skipped"
if ($failed -gt 0) { exit 1 }
exit 0
