param(
    [ValidateSet("Menu", "Full", "Repair", "Database", "MeterSetup", "HealthCheck", "Evidence")]
    [string]$Mode = "Menu",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ApiBaseUrl = "http://127.0.0.1:5000",
    [string]$BackendTaskName = "EnergyMonitoringBackend",
    [switch]$NonInteractive,
    [switch]$SkipDatabase,
    [switch]$SkipFrontendBuild,
    [switch]$SkipMeterTrial,
    [switch]$CreateDatabaseIfMissing,
    [switch]$RunAsCurrentUser
)

Set-StrictMode -Version 2.0

. (Join-Path $PSScriptRoot "lib\DeploymentToolkit.ps1")

function Show-DeploymentMenu {
    Write-Host ""
    Write-Host "Energy Monitoring Deployment Tool"
    Write-Host ""
    Write-Host "1. Full Setup"
    Write-Host "2. Repair Setup"
    Write-Host "3. Database Only"
    Write-Host "4. Meter/COM Setup Only"
    Write-Host "5. Health Check Only"
    Write-Host "6. Collect Evidence"
    Write-Host "7. Exit"
    Write-Host ""

    $choice = Read-Host "Select an option"
    switch ($choice) {
        "1" { return "Full" }
        "2" { return "Repair" }
        "3" { return "Database" }
        "4" { return "MeterSetup" }
        "5" { return "HealthCheck" }
        "6" { return "Evidence" }
        default { return "Exit" }
    }
}

if ($Mode -eq "Menu") {
    if ($NonInteractive) {
        throw "-Mode is required when -NonInteractive is used."
    }
    $selectedMode = Show-DeploymentMenu
    if ($selectedMode -eq "Exit") {
        Write-Host "Exiting."
        exit 0
    }
    $Mode = $selectedMode
}

$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$interactive = (-not $NonInteractive) -and [Environment]::UserInteractive
$reportRoot = Initialize-DeploymentReport -ProjectRoot $ProjectRoot -Mode $Mode

Write-Host ""
Write-Host "Energy Monitoring Deployment Tool"
Write-Host "Mode: $Mode"
Write-Host "Project root: $ProjectRoot"
Write-Host "Report folder: $reportRoot"
Write-Host ""

try {
    Copy-DeploymentArtifacts -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
    Save-SanitizedEnv -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
    Save-DetectedComPorts -ReportRoot $reportRoot

    switch ($Mode) {
        "Full" {
            Test-Prerequisites -IncludeFrontend:$true -IncludeDatabase:(-not $SkipDatabase)
            Ensure-EnvFile -ProjectRoot $ProjectRoot -Modify:$true
            & (Join-Path $ProjectRoot "scripts\first_run_setup.ps1") -ProjectRoot $ProjectRoot 2>&1 |
                Set-Content -Path (Join-Path $reportRoot "first-run-setup.txt") -Encoding UTF8
            Add-DeploymentCheck -Status "PASS" -Label "first run setup" -Detail "directories and .env baseline checked" -Category "environment"

            Ensure-PythonEnvironment -ProjectRoot $ProjectRoot -ReportRoot $reportRoot | Out-Null
            if (-not $SkipDatabase) {
                Invoke-DatabaseSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -ApplySchema:$true -CreateDatabase:$true
            }
            Invoke-FrontendStep -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -Build:(-not $SkipFrontendBuild)
            Test-MeterConfiguration -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            Invoke-MeterWizard -ProjectRoot $ProjectRoot -Interactive:$interactive
            if (-not $SkipMeterTrial) {
                Invoke-MeterTrial -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            }
            Invoke-ScheduledTaskSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -TaskName $BackendTaskName -RunAsCurrentUser:$RunAsCurrentUser
            Test-ScheduledTaskState -ReportRoot $reportRoot -TaskName $BackendTaskName
            Invoke-ApiChecks -ApiBaseUrl $ApiBaseUrl -ReportRoot $reportRoot -Required:$false
            Save-LogsTail -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
        }
        "Repair" {
            Test-Prerequisites -IncludeFrontend:$true -IncludeDatabase:(-not $SkipDatabase)
            Ensure-EnvFile -ProjectRoot $ProjectRoot -Modify:$true
            Ensure-PythonEnvironment -ProjectRoot $ProjectRoot -ReportRoot $reportRoot | Out-Null
            if (-not $SkipDatabase) {
                Invoke-DatabaseSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -ApplySchema:$true -CreateDatabase:$true
            }
            Invoke-FrontendStep -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -Build:(-not $SkipFrontendBuild)
            Test-MeterConfiguration -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            Invoke-MeterWizard -ProjectRoot $ProjectRoot -Interactive:$interactive
            if (-not $SkipMeterTrial) {
                Invoke-MeterTrial -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            }
            Invoke-ScheduledTaskSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -TaskName $BackendTaskName -RunAsCurrentUser:$RunAsCurrentUser
            Test-ScheduledTaskState -ReportRoot $reportRoot -TaskName $BackendTaskName
            Invoke-ApiChecks -ApiBaseUrl $ApiBaseUrl -ReportRoot $reportRoot -Required:$false
            Save-LogsTail -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
        }
        "Database" {
            Test-Prerequisites -IncludeFrontend:$false -IncludeDatabase:$true
            Ensure-EnvFile -ProjectRoot $ProjectRoot -Modify:$true
            Ensure-PythonEnvironment -ProjectRoot $ProjectRoot -ReportRoot $reportRoot | Out-Null
            $createDb = [bool]$CreateDatabaseIfMissing
            if ($interactive -and -not $CreateDatabaseIfMissing) {
                $answer = Read-Host "Create configured PostgreSQL database if it is missing? Type YES to allow"
                $createDb = $answer -eq "YES"
            }
            Invoke-DatabaseSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -ApplySchema:$true -CreateDatabase:$createDb
        }
        "MeterSetup" {
            Test-Prerequisites -IncludeFrontend:$false -IncludeDatabase:$false
            Test-PythonEnvironment -ProjectRoot $ProjectRoot
            Test-MeterConfiguration -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            Invoke-MeterWizard -ProjectRoot $ProjectRoot -Interactive:$interactive
            Test-MeterConfiguration -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            if (-not $SkipMeterTrial) {
                Invoke-MeterTrial -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            }
        }
        "HealthCheck" {
            Test-Prerequisites -IncludeFrontend:$true -IncludeDatabase:(-not $SkipDatabase)
            Ensure-EnvFile -ProjectRoot $ProjectRoot -Modify:$false
            Test-PythonEnvironment -ProjectRoot $ProjectRoot
            if (-not $SkipDatabase) {
                Invoke-DatabaseSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -ApplySchema:$false -CreateDatabase:$false
            }
            Invoke-FrontendStep -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -Build:$false
            Test-MeterConfiguration -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            Test-ScheduledTaskState -ReportRoot $reportRoot -TaskName $BackendTaskName
            Invoke-ApiChecks -ApiBaseUrl $ApiBaseUrl -ReportRoot $reportRoot -Required:$false
            Save-LogsTail -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
        }
        "Evidence" {
            Test-Prerequisites -IncludeFrontend:$true -IncludeDatabase:(-not $SkipDatabase)
            Ensure-EnvFile -ProjectRoot $ProjectRoot -Modify:$false
            Test-PythonEnvironment -ProjectRoot $ProjectRoot
            if (-not $SkipDatabase) {
                Invoke-DatabaseSetup -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -ApplySchema:$false -CreateDatabase:$false
            }
            Invoke-FrontendStep -ProjectRoot $ProjectRoot -ReportRoot $reportRoot -Build:$false
            Test-MeterConfiguration -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
            Test-ScheduledTaskState -ReportRoot $reportRoot -TaskName $BackendTaskName
            Invoke-ApiChecks -ApiBaseUrl $ApiBaseUrl -ReportRoot $reportRoot -Required:$false
            Save-LogsTail -ProjectRoot $ProjectRoot -ReportRoot $reportRoot
        }
    }
}
finally {
    $result = Complete-DeploymentReport -ProjectRoot $ProjectRoot -Mode $Mode
    if ($Mode -eq "Evidence") {
        Compress-DeploymentReport -ReportRoot $reportRoot | Out-Null
        $result = Complete-DeploymentReport -ProjectRoot $ProjectRoot -Mode $Mode
    }

    Write-Host ""
    Write-Host "Deployment report written:"
    Write-Host $result.SummaryPath
    Write-Host ""
    if ($result.FailCount -gt 0) {
        Write-Host "Completed with $($result.FailCount) FAIL check(s)." -ForegroundColor Red
        exit 1
    }

    Write-Host "Completed with no FAIL checks." -ForegroundColor Green
}
