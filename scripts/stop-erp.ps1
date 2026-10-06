# Stop what start-erp.ps1 started: the local API, the event worker and the web admin.
#
# start-erp.ps1 declares itself "safe to run manually or from the Windows Startup folder on logon" and starts
# three hidden processes, with nothing to stop them again — the other half of a documented convenience. This
# stops exactly those three, matching the same command-line patterns start-erp.ps1 uses to decide whether
# something is already running, and leaves the Docker infrastructure alone unless asked: postgres/redis/minio
# are shared with ordinary development and stopping them is a bigger decision than stopping the app.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-erp.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-erp.ps1 -IncludeInfrastructure

param(
    [switch]$DryRun,
    [switch]$IncludeInfrastructure
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InfraServices = @("postgres", "redis", "minio")
$stopped = 0

function Stop-MatchingProcess {
    param(
        [string]$Name,
        [string]$Match,
        [string]$Filter = "Name='python.exe' or Name='node.exe'"
    )

    $targets = @(
        Get-CimInstance Win32_Process -Filter $Filter -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*$Match*" }
    )
    if ($targets.Count -eq 0) {
        Write-Host "[ERP] $Name is not running."
        return
    }
    foreach ($target in $targets) {
        if ($DryRun) {
            Write-Host "[ERP] Would stop $Name (pid $($target.ProcessId))."
        } else {
            Write-Host "[ERP] Stopping $Name (pid $($target.ProcessId))..."
            Stop-Process -Id $target.ProcessId -Force -ErrorAction SilentlyContinue
        }
        $script:stopped++
    }
}

function Stop-PortOwner {
    param([int]$Port, [string]$Name)

    $owner = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -First 1
    if (-not $owner) {
        Write-Host "[ERP] Nothing listening on port $Port."
        return
    }
    # Only stop it if it is one of ours, so an unrelated server on the port is left alone.
    $info = Get-CimInstance Win32_Process -Filter "ProcessId=$owner" -ErrorAction SilentlyContinue
    $commandLine = if ($info) { [string]$info.CommandLine } else { "" }
    if ($commandLine -like "*$Root*") {
        if ($DryRun) {
            Write-Host "[ERP] Would stop $Name on port $Port (pid $owner)."
        } else {
            Write-Host "[ERP] Stopping $Name on port $Port (pid $owner)..."
            Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue
        }
        $script:stopped++
    } else {
        Write-Host "[ERP] Port $Port is held by something else (pid $owner); leaving it alone."
    }
}

Set-Location $Root

# Every pattern is anchored on the repository root. A bare "*web-admin*" also matches any unrelated
# program whose installation path contains that name — on this machine it matched the command harness — and a
# stop script that kills the wrong process is worse than no stop script.
Stop-MatchingProcess -Name "API (run_local_api.py)" -Match "*$Root*run_local_api*"
Stop-MatchingProcess -Name "event worker" -Match "*$Root*workers.event_worker*"
Stop-MatchingProcess -Name "web admin" -Match "*$Root*apps\web-admin*"
Stop-PortOwner -Port 8000 -Name "API"
Stop-PortOwner -Port 3000 -Name "web admin"

if ($IncludeInfrastructure) {
    if ($DryRun) {
        Write-Host "[ERP] Would stop infrastructure (postgres, redis, minio)."
    } else {
        Write-Host "[ERP] Stopping infrastructure (postgres, redis, minio)..."
        docker compose stop @InfraServices
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "[ERP] 'docker compose stop' returned $LASTEXITCODE."
        }
    }
} else {
    Write-Host "[ERP] Infrastructure left running (pass -IncludeInfrastructure to stop it too)."
}

if ($stopped -eq 0) {
    Write-Host "[ERP] Nothing to stop."
} else {
    Write-Host "[ERP] Stopped $stopped process(es)."
}
