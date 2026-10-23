# Reload prod nginx after api/web recreate (upstream IP cache).
# Usage: powershell -NoProfile -File scripts/reload-prod-nginx.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod exec -T nginx nginx -t
docker compose -f docker-compose.prod.yml --env-file backend/.env.prod exec -T nginx nginx -s reload
Write-Host "[OK] nginx reloaded"
