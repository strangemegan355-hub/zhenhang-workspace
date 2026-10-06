# Verify the production web-admin serving path: the standalone server, not just the build.
#
# `next build` succeeding says nothing about whether the built app can be *served*. That path is
# `node apps/web-admin/server.js` under `.next/standalone` — what the web image runs and what start-erp.ps1
# starts — and it needs `.next/static` and `public` copied into the standalone tree, which is what
# Sync-WebStandaloneAssets does at start time. Miss that copy and the page still returns 200 while every
# stylesheet and chunk 404s, so this checks the HTML *and* every asset it references, not just the status code.
#
# It starts the server on its own port, probes it, and always stops it again — including on failure — because
# a verification script that leaves a server behind is worse than no script.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-web-standalone.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-web-standalone.ps1 -Port 3200 -SkipBuild
#
# Exits 0 when the production page and all of its assets are served, 1 otherwise.

param(
    [int]$Port = 3100,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$App = Join-Path $Root "apps\web-admin"
$StandaloneRoot = Join-Path $App ".next\standalone"
$Server = Join-Path $StandaloneRoot "apps\web-admin\server.js"
$Npm = "C:\Program Files\nodejs\npm.cmd"
$Node = "C:\Program Files\nodejs\node.exe"

function Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $Server)) {
    if ($SkipBuild) {
        Fail "the standalone tree is missing ($Server). Run without -SkipBuild, or run: npm run build -w web-admin"
    }
    if (-not (Test-Path $Npm)) { Fail "npm not found at $Npm; a build is required first" }
    Write-Host "[WEB] Building web-admin (first run, may take a few minutes)..."
    Push-Location $Root
    & $Npm run build -w web-admin
    $buildCode = $LASTEXITCODE
    Pop-Location
    if ($buildCode -ne 0) { Fail "the build failed with exit $buildCode" }
    if (-not (Test-Path $Server)) { Fail "the build finished but $Server still does not exist" }
}

if (-not (Test-Path $Node)) { Fail "node not found at $Node" }

# The same asset sync start-erp.ps1 performs before starting the server.
$staticSrc = Join-Path $App ".next\static"
$staticDst = Join-Path $StandaloneRoot "apps\web-admin\.next\static"
$publicSrc = Join-Path $App "public"
$publicDst = Join-Path $StandaloneRoot "apps\web-admin\public"
if (Test-Path $staticSrc) { Copy-Item -Path $staticSrc -Destination $staticDst -Recurse -Force }
if (Test-Path $publicSrc) { Copy-Item -Path $publicSrc -Destination $publicDst -Recurse -Force }

$env:PORT = "$Port"
$env:HOSTNAME = "127.0.0.1"
$env:NODE_ENV = "production"
$env:NEXT_TELEMETRY_DISABLED = "1"
$outLog = Join-Path $env:TEMP "verify-web-standalone.out.log"
$errLog = Join-Path $env:TEMP "verify-web-standalone.err.log"
$process = $null
$exitCode = 0

try {
    Write-Host "[WEB] Starting the standalone server on port $Port..."
    $process = Start-Process -FilePath $Node -ArgumentList "apps\web-admin\server.js" `
        -WorkingDirectory $StandaloneRoot -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog

    $page = $null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 700
        try {
            $response = Invoke-WebRequest "http://127.0.0.1:$Port/login" -UseBasicParsing -TimeoutSec 4
            if ($response.StatusCode -eq 200) { $page = $response; break }
        } catch { }
    }

    if ($null -eq $page) {
        Write-Host "[FAIL] /login did not answer 200 within 21 seconds." -ForegroundColor Red
        if (Test-Path $errLog) {
            Write-Host "  last lines of $errLog :"
            Get-Content $errLog -ErrorAction SilentlyContinue | Select-Object -Last 8 | ForEach-Object { "    $_" }
        }
        $exitCode = 1
    } else {
        $html = $page.Content
        Write-Host "[ OK ] /login -> 200, $($html.Length) bytes"
        if ($html -notmatch "__next") { Write-Host "[FAIL] the response has no __next marker, so it is probably not the app" -ForegroundColor Red; $exitCode = 1 }
        if ($html -notmatch "<title") { Write-Host "[FAIL] the response has no <title element" -ForegroundColor Red; $exitCode = 1 }

        $assets = [regex]::Matches($html, '/_next/static/[^"''<> ]+\.(js|css)') | ForEach-Object { $_.Value } | Select-Object -Unique
        if (($assets | Measure-Object).Count -eq 0) {
            Write-Host "[FAIL] the page references no /_next/static assets; the standalone tree is incomplete" -ForegroundColor Red
            $exitCode = 1
        } else {
            $failed = @()
            foreach ($asset in $assets) {
                try {
                    $a = Invoke-WebRequest "http://127.0.0.1:$Port$asset" -UseBasicParsing -TimeoutSec 6
                    if ($a.StatusCode -ne 200) { $failed += "$asset -> $($a.StatusCode)" }
                } catch {
                    $failed += "$asset -> $($_.Exception.Message)"
                }
            }
            $count = ($assets | Measure-Object).Count
            if ($failed.Count -eq 0) {
                Write-Host "[ OK ] all $count referenced static assets are served"
            } else {
                Write-Host "[FAIL] $($failed.Count) of $count static assets are not served:" -ForegroundColor Red
                $failed | Select-Object -First 8 | ForEach-Object { "    $_" }
                $exitCode = 1
            }
        }
    }
} finally {
    if ($process) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 600
    }
    if ($process -and (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) {
        Write-Host "[WARN] the server (pid $($process.Id)) is still running" -ForegroundColor Yellow
    }
}

if ($exitCode -eq 0) {
    Write-Host "[ OK ] the production web admin is served from the standalone build on port $Port"
} else {
    Write-Host "[FAIL] the production web admin did not serve correctly" -ForegroundColor Red
}
exit $exitCode
