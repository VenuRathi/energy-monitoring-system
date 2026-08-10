param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [ValidateSet("", "Start", "Stop", "Refresh")]
    [string]$Action = ""
)

$ErrorActionPreference = "Stop"

function Get-ConfiguredApiBaseUrl {
    $envPath = Join-Path $ProjectRoot ".env"
    $hostValue = "127.0.0.1"
    $portValue = "5000"
    if (Test-Path $envPath) {
        foreach ($line in Get-Content -LiteralPath $envPath) {
            $parts = $line.Trim() -split "=", 2
            if ($parts.Count -ne 2) { continue }
            switch ($parts[0].Trim()) {
                "API_HOST" { if ($parts[1].Trim()) { $hostValue = $parts[1].Trim() } }
                "API_PORT" { if ($parts[1].Trim()) { $portValue = $parts[1].Trim() } }
            }
        }
    }
    if ($hostValue -in @("0.0.0.0", "::", "*")) { $hostValue = "127.0.0.1" }
    return "http://{0}:{1}" -f $hostValue, $portValue
}

$apiBaseUrl = Get-ConfiguredApiBaseUrl
$watchdogLauncher = Join-Path $ProjectRoot "scripts\run_backend_watchdog.vbs"
$stopScript = Join-Path $ProjectRoot "scripts\stop_backend_task.ps1"
$powershellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$wscriptExe = Join-Path $env:SystemRoot "System32\wscript.exe"
$backendTaskName = "EnergyMonitoringBackend"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-BackendScheduledTask {
    try {
        return Get-ScheduledTask -TaskName $backendTaskName -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Invoke-ElevatedControlAction {
    param([ValidateSet("Start", "Stop")][string]$RequestedAction)

    $argumentList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath,
        "-ProjectRoot", $ProjectRoot,
        "-Action", $RequestedAction
    )

    try {
        $elevatedProcess = Start-Process -FilePath $powershellExe `
            -Verb RunAs `
            -ArgumentList $argumentList `
            -WorkingDirectory $ProjectRoot `
            -WindowStyle Hidden `
            -Wait `
            -PassThru
    }
    catch {
        throw "Administrator approval was cancelled or unavailable. The project was not changed. $($_.Exception.Message)"
    }

    if ($elevatedProcess.ExitCode -ne 0) {
        throw "Administrator-elevated $RequestedAction failed with exit code $($elevatedProcess.ExitCode). Review logs\backend_watchdog.log."
    }

    return "Administrator-elevated $RequestedAction completed successfully."
}

function Get-ApiStatus {
    try {
        return Invoke-RestMethod -Uri "$apiBaseUrl/api/status" -Method Get -TimeoutSec 4
    }
    catch {
        return $null
    }
}

function Get-ApiMeters {
    try {
        return @(Invoke-RestMethod -Uri "$apiBaseUrl/api/meters" -Method Get -TimeoutSec 4)
    }
    catch {
        return @()
    }
}

function Get-PortListeners {
    $port = ([uri]$apiBaseUrl).Port
    return @(netstat -ano | Select-String ("127\.0\.0\.1:{0}.*LISTENING" -f $port))
}

function Start-ProjectSystem {
    if (-not (Test-Path $watchdogLauncher)) {
        throw "Watchdog launcher not found: $watchdogLauncher"
    }

    if (Get-ApiStatus) {
        return "Backend is already reachable at $apiBaseUrl. No duplicate watchdog was started."
    }

    $scheduledTask = Get-BackendScheduledTask
    if ($scheduledTask) {
        if (-not (Test-IsAdministrator)) {
            return Invoke-ElevatedControlAction -RequestedAction "Start"
        }

        Start-ScheduledTask -TaskName $backendTaskName -ErrorAction Stop
        $deadline = (Get-Date).AddSeconds(45)
        do {
            Start-Sleep -Seconds 2
            $status = Get-ApiStatus
            if ($status) {
                return "Scheduled backend task started and polling became reachable at $apiBaseUrl. Dashboard was not opened."
            }
        } while ((Get-Date) -lt $deadline)

        throw "Scheduled backend task was started, but the backend did not become reachable within 45 seconds. Check logs\backend_watchdog.log and logs\energy_monitoring.log."
    }

    Start-Process -FilePath $wscriptExe `
        -ArgumentList @("`"$watchdogLauncher`"") `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds(45)
    do {
        Start-Sleep -Seconds 2
        $status = Get-ApiStatus
        if ($status) {
            return "Backend and polling became reachable at $apiBaseUrl. Dashboard was not opened."
        }
    } while ((Get-Date) -lt $deadline)

    throw "Watchdog was launched, but the backend did not become reachable within 45 seconds. Check logs\backend_watchdog.log and logs\energy_monitoring.log."
}

function Stop-ProjectSystem {
    if (-not (Test-Path $stopScript)) {
        throw "Safe stop script not found: $stopScript"
    }

    if (-not (Test-IsAdministrator)) {
        return Invoke-ElevatedControlAction -RequestedAction "Stop"
    }

    $stopProcess = Start-Process -FilePath $powershellExe `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $stopScript,
            "-ProjectRoot", $ProjectRoot
        ) `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -Wait `
        -PassThru

    if ($stopProcess.ExitCode -ne 0) {
        throw "The existing safe stop procedure returned exit code $($stopProcess.ExitCode)."
    }

    $deadline = (Get-Date).AddSeconds(15)
    do {
        Start-Sleep -Seconds 1
        $listeners = Get-PortListeners
        if ($listeners.Count -eq 0) {
            return "Project backend stopped; port $(([uri]$apiBaseUrl).Port) has no local project listener."
        }
    } while ((Get-Date) -lt $deadline)

    throw "Stop procedure completed, but port $(([uri]$apiBaseUrl).Port) is still listening. No unrelated process was stopped."
}

function Get-ServiceStatusText {
    $services = @(Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue)
    if (-not $services) { return "Not found" }
    $running = @($services | Where-Object Status -eq "Running")
    if ($running.Count -eq $services.Count) { return "Healthy / Running" }
    return (($services | ForEach-Object { "$($_.Name): $($_.Status)" }) -join "; ")
}

function Get-StatusSnapshot {
    $status = Get-ApiStatus
    $meters = Get-ApiMeters
    $m1 = @($meters | Where-Object meter_id -eq "MTR-001")[0]
    $m2 = @($meters | Where-Object meter_id -eq "MTR-002")[0]
    $listener = Get-PortListeners
    [pscustomobject]@{
        ApiReachable = [bool]$status
        ApiStatus = if ($status) { [string]$status.apiStatus } else { "Unreachable" }
        Database = if ($status) { [string]$status.databaseStatus } else { "Unknown" }
        PostgreSQL = Get-ServiceStatusText
        Polling = if ($status) { if ($status.polling.running) { "Running" } else { "Stopped" } } else { "Unknown" }
        CycleCount = if ($status) { [string]$status.polling.totalCyclesCompleted } else { "-" }
        MTR001 = if ($m1) { "$($m1.status) / $($m1.com_port) / slave $($m1.slave_id)" } else { "Not reported" }
        MTR002 = if ($m2) { "$($m2.status) / $($m2.com_port) / slave $($m2.slave_id)" } else { "Not reported" }
        Port5000 = if ($listener.Count -gt 0) { "Listening" } else { "Stopped" }
        ApiHost = ([uri]$apiBaseUrl).Host
    }
}

if ($Action) {
    switch ($Action) {
        "Start" { Start-ProjectSystem; exit 0 }
        "Stop" { Stop-ProjectSystem; exit 0 }
        "Refresh" { Get-StatusSnapshot | ConvertTo-Json -Depth 5; exit 0 }
    }
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "Plant Energy Monitor Control"
$form.StartPosition = "CenterScreen"
$form.Size = New-Object System.Drawing.Size(620, 430)
$form.MinimumSize = New-Object System.Drawing.Size(620, 430)
$form.BackColor = [System.Drawing.Color]::FromArgb(245, 248, 250)

$title = New-Object System.Windows.Forms.Label
$title.Text = "Plant Energy Monitor Control"
$title.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = [System.Drawing.Color]::FromArgb(20, 72, 100)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(22, 18)
$form.Controls.Add($title)

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = "Temporary user-level testing utility - does not open the dashboard."
$subtitle.AutoSize = $true
$subtitle.Location = New-Object System.Drawing.Point(24, 50)
$subtitle.ForeColor = [System.Drawing.Color]::DimGray
$form.Controls.Add($subtitle)

$startButton = New-Object System.Windows.Forms.Button
$startButton.Text = "Start System"
$startButton.Size = New-Object System.Drawing.Size(145, 38)
$startButton.Location = New-Object System.Drawing.Point(22, 82)
$form.Controls.Add($startButton)

$stopButton = New-Object System.Windows.Forms.Button
$stopButton.Text = "Stop System"
$stopButton.Size = New-Object System.Drawing.Size(145, 38)
$stopButton.Location = New-Object System.Drawing.Point(177, 82)
$form.Controls.Add($stopButton)

$refreshButton = New-Object System.Windows.Forms.Button
$refreshButton.Text = "Refresh Status"
$refreshButton.Size = New-Object System.Drawing.Size(145, 38)
$refreshButton.Location = New-Object System.Drawing.Point(332, 82)
$form.Controls.Add($refreshButton)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Ready"
$statusLabel.AutoSize = $false
$statusLabel.Size = New-Object System.Drawing.Size(555, 38)
$statusLabel.Location = New-Object System.Drawing.Point(22, 132)
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(20, 72, 100)
$form.Controls.Add($statusLabel)

$grid = New-Object System.Windows.Forms.DataGridView
$grid.Location = New-Object System.Drawing.Point(22, 180)
$grid.Size = New-Object System.Drawing.Size(555, 170)
$grid.ReadOnly = $true
$grid.AllowUserToAddRows = $false
$grid.AllowUserToDeleteRows = $false
$grid.RowHeadersVisible = $false
$grid.AutoSizeColumnsMode = "Fill"
$grid.BackgroundColor = [System.Drawing.Color]::White
$grid.Columns.Add("Check", "Check") | Out-Null
$grid.Columns.Add("Status", "Status") | Out-Null
$form.Controls.Add($grid)

$footer = New-Object System.Windows.Forms.Label
$footer.Text = "Local-only: $apiBaseUrl | Start/Stop uses the existing watchdog and safe stop procedure."
$footer.AutoSize = $true
$footer.Location = New-Object System.Drawing.Point(22, 365)
$footer.ForeColor = [System.Drawing.Color]::DimGray
$form.Controls.Add($footer)

function Update-UiStatus {
    try {
        $snapshot = Get-StatusSnapshot
        $grid.Rows.Clear()
        foreach ($property in @("ApiStatus", "Database", "PostgreSQL", "Polling", "MTR001", "MTR002", "Port5000", "CycleCount")) {
            $label = switch ($property) {
                "ApiStatus" { "Backend/API" }
                "MTR001" { "MTR-001" }
                "MTR002" { "MTR-002" }
                "Port5000" { "Backend port" }
                "CycleCount" { "Polling cycles" }
                default { $property }
            }
            $grid.Rows.Add($label, [string]$snapshot.$property) | Out-Null
        }
        $statusLabel.Text = "Last refreshed: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
        $statusLabel.ForeColor = if ($snapshot.ApiReachable) { [System.Drawing.Color]::DarkGreen } else { [System.Drawing.Color]::DarkOrange }
    }
    catch {
        $statusLabel.Text = "Status refresh failed: $($_.Exception.Message)"
        $statusLabel.ForeColor = [System.Drawing.Color]::DarkRed
    }
}

$startButton.Add_Click({
    $startButton.Enabled = $false
    $stopButton.Enabled = $false
    try { $statusLabel.Text = Start-ProjectSystem } catch { $statusLabel.Text = $_.Exception.Message }
    finally { $startButton.Enabled = $true; $stopButton.Enabled = $true; Update-UiStatus }
})

$stopButton.Add_Click({
    $startButton.Enabled = $false
    $stopButton.Enabled = $false
    try { $statusLabel.Text = Stop-ProjectSystem } catch { $statusLabel.Text = $_.Exception.Message }
    finally { $startButton.Enabled = $true; $stopButton.Enabled = $true; Update-UiStatus }
})

$refreshButton.Add_Click({ Update-UiStatus })
$form.Add_Shown({ Update-UiStatus })
[System.Windows.Forms.Application]::Run($form)
