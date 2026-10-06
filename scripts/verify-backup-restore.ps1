# Restore drill: prove a dump restores, instead of assuming it does.
#
# `deploy/backup/backup-postgres.sh` is careful — it dumps to a temporary name and moves it into place, because
# redirecting straight into the backup file leaves a truncated file that keeps a backup's name and even passes
# `gzip -t`. The docs describe a restore recipe in prose. What no command in this repository did was **restore
# something and compare it**, which is the only way to know a backup is worth having: a backup that has never
# been restored is a file, not a backup.
#
# This dumps a live database, restores it into a scratch database in the same server, and compares the two
# table by table. Table count alone is too blunt to count as evidence — a restore that dropped every row and
# kept every table would pass it — so the comparison is per-table row counts, plus the alembic revision so a
# schema that restored without its migration head is caught too.
#
# Two things this script learned the hard way:
#
#   * The container is named explicitly. Other stacks run on this machine, and a glob for "postgres" can reach
#     one of theirs.
#   * **Native stderr must not be allowed to terminate the run.** The first version set
#     `$ErrorActionPreference = "Stop"` and called `drop database if exists`, which prints a NOTICE to stderr
#     whenever the scratch database is absent; PowerShell turns a native command's stderr into a terminating
#     error, so the script aborted with exit 1 — and only happened to pass the first time because a manual run
#     had left the scratch database behind. An unattended drill would have failed on its first run and the
#     failure would have looked like a bad backup. Native calls now run with `Continue` and are judged by
#     `$LASTEXITCODE`, and the drop is skipped when the database is not there, so the NOTICE is not produced at
#     all.
#
# Usage:
#   powershell -File scripts/verify-backup-restore.ps1
#   powershell -File scripts/verify-backup-restore.ps1 -Container shengtaixitong-postgres-1

[CmdletBinding()]
param(
    [string]$Container = "integration_tests-postgres-1",
    [string]$Database = "erp_db",
    [string]$DbUser = "erp",
    [string]$Scratch = "erp_restore_check",
    [int]$MinimumTables = 50
)

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$work = Join-Path ([System.IO.Path]::GetTempPath()) "erp-restore-drill-$stamp"
New-Item -ItemType Directory -Path $work -Force | Out-Null

# query_to_xml runs a per-table count in one statement, which avoids N round trips and keeps the SQL free of the
# quoting that has bitten every inline `count(*)` in this session.
$countsSql = @'
select relname || '|' || (
  xpath('/row/c/text()',
        query_to_xml(format('select count(1) as c from %I.%I', schemaname, relname), false, true, '')))[1]::text
from pg_stat_user_tables
order by relname;
'@
$countsFile = Join-Path $work "counts.sql"
[System.IO.File]::WriteAllText($countsFile, $countsSql, (New-Object System.Text.UTF8Encoding($false)))
$dumpFile = Join-Path $work "erp_dump.sql"

function Invoke-Docker {
    # Native commands write notices to stderr; with ErrorActionPreference = Stop that terminates the script, so
    # it is relaxed here and every caller judges the result by its exit code instead.
    param([string[]]$DockerArguments, [string]$StandardInput)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($null -ne $StandardInput) {
            $output = $StandardInput | & docker @DockerArguments 2>&1
        } else {
            $output = & docker @DockerArguments 2>&1
        }
        return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = @($output) }
    } finally {
        $ErrorActionPreference = $previous
    }
}

function Invoke-Sql {
    param([string]$DatabaseName, [string]$Statement)
    $result = Invoke-Docker -DockerArguments @("exec", "-i", $container, "psql", "-U", $DbUser, "-d", $DatabaseName, "-t", "-A", "-c", $Statement)
    if ($result.ExitCode -ne 0) {
        throw "psql against ${DatabaseName} failed: $($result.Output | Select-Object -Last 3)"
    }
    return $result.Output
}

function ConvertTo-Number {
    # `[int]"0"` is 48, not 0: casting a one-character string to [int] gives its character code. Every count
    # here arrives as a string, so the numeric cast has to be explicit. This bit twice — the presence check
    # concluded the scratch database always existed, and the row-count comparison compared character codes,
    # which are wrong *symmetrically* and therefore still compare equal.
    param([string]$Text)
    return [int]::Parse($Text.Trim(), [System.Globalization.CultureInfo]::InvariantCulture)
}

Write-Host "=== restore drill: $Container / $Database -> $Scratch ===" -ForegroundColor Cyan
$scratchExists = $false
try {
    Write-Host "  1. dumping $Database"
    # Straight to a file through cmd's redirection, with no PowerShell in the data path. Capturing pg_dump into
    # a PowerShell string array and writing it back re-encoded the text (PowerShell 5.1 decodes native output
    # with the ANSI code page) and merged stderr into it, which shifted field boundaries inside COPY blocks:
    # psql then failed with `invalid input syntax for type uuid: "f"` on a dump that is perfectly valid.
    $dumpCommand = "docker exec -i $container pg_dump -U $DbUser --no-owner --no-privileges $Database > `"$dumpFile`""
    & cmd /c $dumpCommand
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit $LASTEXITCODE" }
    $dumpBytes = (Get-Item $dumpFile).Length
    if ($dumpBytes -lt 1024) { throw "the dump is only $dumpBytes bytes, which cannot be a database" }
    Write-Host "     $([Math]::Round($dumpBytes / 1KB, 1)) KB written"

    Write-Host "  2. recreating the scratch database"
    $present = Invoke-Sql -DatabaseName "postgres" -Statement "select count(1) from pg_database where datname = '$Scratch'"
    if ((ConvertTo-Number $present[0]) -gt 0) {
        Invoke-Sql -DatabaseName "postgres" -Statement "drop database $Scratch" | Out-Null
    }
    Invoke-Sql -DatabaseName "postgres" -Statement "create database $Scratch" | Out-Null
    $scratchExists = $true

    Write-Host "  3. restoring into $Scratch"
    # `cmd /c` again, feeding the file itself: PowerShell would re-encode it on the way through a pipeline.
    $restoreLog = Join-Path $work "restore.log"
    $restoreCommand = "docker exec -i $container psql -U $DbUser -d $Scratch -q -v ON_ERROR_STOP=1 < `"$dumpFile`" > `"$restoreLog`" 2>&1"
    & cmd /c $restoreCommand
    $restoreExit = $LASTEXITCODE
    $restoreText = Get-Content $restoreLog -Raw
    if ($restoreExit -ne 0) { throw "restore failed (exit $restoreExit): $($restoreText -split "`n" | Select-Object -Last 5)" }
    $errors = @(($restoreText -split "`n") | Where-Object { $_ -match 'ERROR' })
    if ($errors.Count -gt 0) { throw "restore reported errors: $($errors | Select-Object -First 3)" }
    Write-Host "     restored with no errors"

    Write-Host "  4. comparing table by table"
    $countsSqlText = Get-Content $countsFile -Raw
    $source = Invoke-Docker -DockerArguments @("exec", "-i", $container, "psql", "-U", $DbUser, "-d", $Database, "-t", "-A", "-f", "-") -StandardInput $countsSqlText
    if ($source.ExitCode -ne 0) { throw "counting rows in ${Database} failed: $($source.Output | Select-Object -Last 3)" }
    $restored = Invoke-Docker -DockerArguments @("exec", "-i", $container, "psql", "-U", $DbUser, "-d", $Scratch, "-t", "-A", "-f", "-") -StandardInput $countsSqlText
    if ($restored.ExitCode -ne 0) { throw "counting rows in ${Scratch} failed: $($restored.Output | Select-Object -Last 3)" }

    $toCounts = {
        param($lines)
        $map = @{}
        foreach ($line in $lines) {
            $parts = $line -split '\|'
            if ($parts.Count -eq 2 -and $parts[1].Trim() -match '^\d+$') { $map[$parts[0]] = [int]::Parse($parts[1].Trim()) }
        }
        return $map
    }
    $sourceCounts = & $toCounts $source.Output
    $scratchCounts = & $toCounts $restored.Output

    # A comparison over nothing passes silently, so refuse to report on a suspiciously small set.
    if ($sourceCounts.Count -lt $MinimumTables) {
        throw "only $($sourceCounts.Count) tables were compared, fewer than the $MinimumTables expected; the comparison itself is suspect"
    }

    $mismatches = @()
    foreach ($table in ($sourceCounts.Keys | Sort-Object)) {
        $expected = $sourceCounts[$table]
        $actual = if ($scratchCounts.ContainsKey($table)) { $scratchCounts[$table] } else { -1 }
        if ($expected -ne $actual) { $mismatches += "      $table : source $expected, restored $actual" }
    }
    $totalRows = ($sourceCounts.Values | Measure-Object -Sum).Sum
    Write-Host "     compared $($sourceCounts.Count) tables, $totalRows rows in total"

    $sourceRevision = @(Invoke-Sql -DatabaseName $Database -Statement "select version_num from alembic_version")[0]
    $scratchRevision = @(Invoke-Sql -DatabaseName $Scratch -Statement "select version_num from alembic_version")[0]
    Write-Host "     alembic revision: source $sourceRevision, restored $scratchRevision"

    $failed = $false
    if ($mismatches.Count -gt 0) {
        Write-Host "  FAIL: row counts differ" -ForegroundColor Red
        $mismatches | ForEach-Object { Write-Host $_ }
        $failed = $true
    }
    if ($sourceRevision -ne $scratchRevision) {
        Write-Host "  FAIL: the restored schema is at a different migration revision" -ForegroundColor Red
        $failed = $true
    }
    if ($failed) { exit 1 }

    Write-Host "  PASS: every table restored with the same row count and the same alembic revision" -ForegroundColor Green
    exit 0
}
finally {
    if ($scratchExists) {
        try { Invoke-Sql -DatabaseName "postgres" -Statement "drop database if exists $Scratch" | Out-Null } catch { }
    }
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
