param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$PsqlPath = "",
    [switch]$ConfirmDrop
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

    foreach ($candidate in @("D:\PostGreSQL\bin\psql.exe", "D:\PostgreSQL\bin\psql.exe")) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Unable to find psql.exe. Add PostgreSQL bin to PATH or pass -PsqlPath explicitly."
}

if (-not $ConfirmDrop) {
    throw "This script is destructive. Re-run with -ConfirmDrop only after backup, dashboard validation, and report validation."
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
        -c "DO $$ DECLARE legacy_count bigint; current_count bigint; BEGIN IF to_regclass('readings_legacy') IS NULL THEN RAISE NOTICE 'readings_legacy is already absent.'; RETURN; END IF; SELECT COUNT(*) INTO legacy_count FROM readings_legacy; SELECT COUNT(*) INTO current_count FROM readings; IF legacy_count <> current_count THEN RAISE EXCEPTION 'Refusing to drop readings_legacy because row counts differ: legacy %, current %', legacy_count, current_count; END IF; DROP TABLE readings_legacy; RAISE NOTICE 'Dropped readings_legacy after validating matching row count %.', current_count; END $$;"

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to drop readings_legacy with exit code $LASTEXITCODE."
    }
}
finally {
    $env:PGPASSWORD = $previousPassword
}
