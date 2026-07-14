param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$BackupRoot = "",
    [string]$PgDumpPath = "",
    [int]$RetentionDays = 14
)

function Read-DotEnvFile {
    param([string]$Path)

    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }

        $separatorIndex = $trimmed.IndexOf("=")
        if ($separatorIndex -lt 1) {
            continue
        }

        $key = $trimmed.Substring(0, $separatorIndex).Trim()
        $value = $trimmed.Substring($separatorIndex + 1).Trim()
        $values[$key] = $value
    }

    return $values
}

function Resolve-PgDumpPath {
    param([string]$PreferredPath)

    if ($PreferredPath -and (Test-Path $PreferredPath)) {
        return (Resolve-Path $PreferredPath).Path
    }

    $command = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $commonRoots = @(
        "C:\Program Files\PostgreSQL",
        "C:\Program Files (x86)\PostgreSQL"
    )

    foreach ($root in $commonRoots) {
        if (-not (Test-Path $root)) {
            continue
        }

        $candidate = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "bin\pg_dump.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1

        if ($candidate) {
            return $candidate
        }
    }

    throw "Unable to find pg_dump.exe. Add PostgreSQL bin to PATH or pass -PgDumpPath explicitly."
}

$envPath = Join-Path $ProjectRoot ".env"
$envValues = Read-DotEnvFile -Path $envPath

$dbHost = if ($envValues.ContainsKey("DB_HOST")) { $envValues["DB_HOST"] } else { "127.0.0.1" }
$dbPort = if ($envValues.ContainsKey("DB_PORT")) { $envValues["DB_PORT"] } else { "5432" }
$dbName = if ($envValues.ContainsKey("DB_NAME")) { $envValues["DB_NAME"] } else { "energy_monitoring" }
$dbUser = if ($envValues.ContainsKey("DB_USER")) { $envValues["DB_USER"] } else { "postgres" }
$dbPassword = if ($envValues.ContainsKey("DB_PASSWORD")) { $envValues["DB_PASSWORD"] } else { "" }

if (-not $BackupRoot) {
    $BackupRoot = Join-Path $ProjectRoot "backups"
}

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$pgDumpExe = Resolve-PgDumpPath -PreferredPath $PgDumpPath
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupFile = Join-Path $BackupRoot "${dbName}_${timestamp}.dump"

$previousPassword = $env:PGPASSWORD
$env:PGPASSWORD = $dbPassword

try {
    & $pgDumpExe -h $dbHost -p $dbPort -U $dbUser -d $dbName -F c -f $backupFile
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed with exit code $LASTEXITCODE."
    }
}
finally {
    $env:PGPASSWORD = $previousPassword
}

if ($RetentionDays -gt 0) {
    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    Get-ChildItem -Path $BackupRoot -Filter "*.dump" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Host "Backup created: $backupFile"
