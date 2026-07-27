param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$PsqlPath = ""
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

function Resolve-PsqlPath {
    param([string]$PreferredPath)

    if ($PreferredPath -and (Test-Path $PreferredPath)) {
        return (Resolve-Path $PreferredPath).Path
    }

    $command = Get-Command psql -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $commonCandidates = @(
        "D:\PostGreSQL\bin\psql.exe",
        "D:\PostgreSQL\bin\psql.exe"
    )

    foreach ($candidate in $commonCandidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
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
            ForEach-Object { Join-Path $_.FullName "bin\psql.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1

        if ($candidate) {
            return $candidate
        }
    }

    throw "Unable to find psql.exe. Add PostgreSQL bin to PATH or pass -PsqlPath explicitly."
}

$envPath = Join-Path $ProjectRoot ".env"
$envValues = Read-DotEnvFile -Path $envPath

$dbHost = if ($envValues.ContainsKey("DB_HOST")) { $envValues["DB_HOST"] } else { "127.0.0.1" }
$dbPort = if ($envValues.ContainsKey("DB_PORT")) { $envValues["DB_PORT"] } else { "5432" }
$dbName = if ($envValues.ContainsKey("DB_NAME")) { $envValues["DB_NAME"] } else { "energy_monitoring" }
$dbUser = if ($envValues.ContainsKey("DB_USER")) { $envValues["DB_USER"] } else { "postgres" }
$dbPassword = if ($envValues.ContainsKey("DB_PASSWORD")) { $envValues["DB_PASSWORD"] } else { "" }

$psqlExe = Resolve-PsqlPath -PreferredPath $PsqlPath
$previousPassword = $env:PGPASSWORD
$env:PGPASSWORD = $dbPassword

try {
    & $psqlExe -h $dbHost -p $dbPort -U $dbUser -d $dbName -v ON_ERROR_STOP=1 `
        -c "SELECT current_database() AS database_name, now() AS checked_at;" `
        -c "SELECT c.relkind AS readings_relkind, CASE c.relkind WHEN 'p' THEN 'partitioned' WHEN 'r' THEN 'plain_table' ELSE c.relkind::text END AS readings_table_type FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = current_schema() AND c.relname = 'readings';" `
        -c "SELECT COUNT(*) AS readings_count, MIN(timestamp) AS oldest_reading, MAX(timestamp) AS newest_reading FROM readings;" `
        -c "SELECT COUNT(*) AS partition_count FROM pg_inherits WHERE inhparent = 'readings'::regclass;" `
        -c "SELECT column_default AS readings_id_default FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'readings' AND column_name = 'id';" `
        -c "SELECT COUNT(*) AS duplicate_groups FROM (SELECT meter_id, timestamp, timestamp_source FROM readings GROUP BY meter_id, timestamp, timestamp_source HAVING COUNT(*) > 1) duplicates;" `
        -c "SELECT COUNT(*) AS hourly_rows, MIN(hour_ts) AS oldest_hour, MAX(hour_ts) AS newest_hour FROM hourly_readings;" `
        -c "SELECT name, setting, unit, pending_restart FROM pg_settings WHERE name IN ('shared_buffers','wal_buffers','max_wal_size','checkpoint_timeout','checkpoint_completion_target','autovacuum_vacuum_scale_factor','autovacuum_analyze_scale_factor','log_min_duration_statement') ORDER BY name;" `
        -c "SELECT name, setting, applied, error FROM pg_file_settings WHERE name IN ('shared_buffers','wal_buffers') ORDER BY name, setting;"

    if ($LASTEXITCODE -ne 0) {
        throw "Database hardening verification failed with exit code $LASTEXITCODE."
    }
}
finally {
    $env:PGPASSWORD = $previousPassword
}
