# Auto-start ShengTai ERP (hybrid mode for Windows):
#   Docker: postgres + redis + minio
#   Local:   FastAPI + event worker + Next.js web-admin
#
# Safe to run manually or from the Windows Startup folder on logon.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Npm = "C:\Program Files\nodejs\npm.cmd"
$Node = "C:\Program Files\nodejs\node.exe"
$LogDir = Join-Path $Root "logs"
$WebBuildId = Join-Path $Root "apps\web-admin\.next\BUILD_ID"
$WebStandaloneServer = Join-Path $Root "apps\web-admin\.next\standalone\apps\web-admin\server.js"
$WebStandaloneRoot = Join-Path $Root "apps\web-admin\.next\standalone"
$InfraServices = @("postgres", "redis", "minio")

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $Root

function Wait-DockerReady {
    param([int]$TimeoutSeconds = 180)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Start-Sleep -Seconds 5
    }
    return $false
}

function Test-PortListening {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Test-PythonProcess {
    param([string]$Match)
    return [bool](
        Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*$Match*" }
    )
}

function Test-NodeWebServer {
    return [bool](
        Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*web-admin*" -or $_.CommandLine -like "*next*" }
    )
}

function Sync-WebStandaloneAssets {
    $staticSrc = Join-Path $Root "apps\web-admin\.next\static"
    $staticDst = Join-Path $WebStandaloneRoot "apps\web-admin\.next\static"
    $publicSrc = Join-Path $Root "apps\web-admin\public"
    $publicDst = Join-Path $WebStandaloneRoot "apps\web-admin\public"

    if (Test-Path $staticSrc) {
        Copy-Item -Path $staticSrc -Destination $staticDst -Recurse -Force
    }
    if (Test-Path $publicSrc) {
        Copy-Item -Path $publicSrc -Destination $publicDst -Recurse -Force
    }
}

function Wait-WebReady {
    param([int]$TimeoutSeconds = 120)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:3000/login" -UseBasicParsing -TimeoutSec 8
            if ($resp.StatusCode -eq 200) { return $true }
        } catch {
            Start-Sleep -Seconds 3
        }
    }
    return $false
}

function Start-BackgroundProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string]$Arguments,
        [string]$WorkingDirectory
    )

    $logOut = Join-Path $LogDir "$Name.out.log"
    $logErr = Join-Path $LogDir "$Name.err.log"
    Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $logOut `
        -RedirectStandardError $logErr | Out-Null
}

if (-not (Wait-DockerReady)) {
    Write-Error "Docker Desktop not ready within 3 minutes."
    exit 1
}

if (-not (Test-Path $Python)) {
    Write-Error "Missing Python venv: $Python"
    exit 1
}

Write-Host "[ERP] Starting infrastructure (postgres, redis, minio)..."
docker compose up -d @InfraServices
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "[ERP] Waiting for PostgreSQL..."
$dbDeadline = (Get-Date).AddMinutes(3)
while ((Get-Date) -lt $dbDeadline) {
    docker compose exec -T postgres pg_isready -U erp -d erp_db 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 3
}

if (-not (Test-PortListening -Port 8000)) {
    Write-Host "[ERP] Starting API..."
    Start-BackgroundProcess `
        -Name "erp-api" `
        -FilePath $Python `
        -Arguments "scripts/run_local_api.py" `
        -WorkingDirectory $Backend
} else {
    Write-Host "[ERP] API already running on port 8000."
}

if (-not (Test-PythonProcess -Match "workers.event_worker")) {
    Write-Host "[ERP] Starting event worker..."
    Start-BackgroundProcess `
        -Name "erp-worker" `
        -FilePath $Python `
        -Arguments "-m workers.event_worker" `
        -WorkingDirectory $Backend
} else {
    Write-Host "[ERP] Event worker already running."
}

$webPid = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -First 1
if ($webPid) {
    Write-Host "[ERP] Restarting web admin..."
    Stop-Process -Id $webPid -Force -ErrorAction SilentlyContinue
    Start-Sleep 2
}

if (-not (Test-Path $Node)) {
    Write-Error "Missing node: $Node"
    exit 1
}

if (-not (Test-Path $WebStandaloneServer)) {
    if (-not (Test-Path $Npm)) {
        Write-Error "Missing npm: $Npm"
        exit 1
    }
    Write-Host "[ERP] Building web admin (first run, may take a few minutes)..."
    & $Npm run build -w web-admin 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "erp-web-build.log")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "[ERP] Syncing web static assets..."
Sync-WebStandaloneAssets

Write-Host "[ERP] Starting web admin (production)..."
Start-BackgroundProcess `
    -Name "erp-web" `
    -FilePath $Node `
    -Arguments "apps\web-admin\server.js" `
    -WorkingDirectory $WebStandaloneRoot

Write-Host "[ERP] Waiting for API health..."
$apiDeadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $apiDeadline) {
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health/live" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) { break }
    } catch {
        Start-Sleep -Seconds 5
    }
}

Write-Host "[ERP] Waiting for web login page..."
if (-not (Wait-WebReady)) {
    Write-Warning "[ERP] Web did not respond in time. Check logs\erp-web.err.log"
} else {
    Write-Host "[ERP] Ready. Open http://localhost:3000/login"
}
