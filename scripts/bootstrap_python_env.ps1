param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$Recreate,
    [switch]$SkipRequirements
)

function Resolve-PythonLauncher {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @{
            Executable = $pythonCommand.Source
            Arguments = @()
            Display = $pythonCommand.Source
        }
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return @{
            Executable = $pyCommand.Source
            Arguments = @("-3")
            Display = "$($pyCommand.Source) -3"
        }
    }

    $commonCandidates = @(
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe",
        "C:\Program Files\Python313\python.exe",
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files\Python311\python.exe"
    )

    foreach ($candidate in $commonCandidates) {
        if (Test-Path $candidate) {
            return @{
                Executable = $candidate
                Arguments = @()
                Display = $candidate
            }
        }
    }

    throw "Python was not found on PATH and no common install path was detected. Install Python first or fix PATH."
}

$venvPath = Join-Path $ProjectRoot ".venv"
$requirementsPath = Join-Path $ProjectRoot "requirements.txt"

if ((Test-Path $venvPath) -and -not $Recreate) {
    Write-Host ".venv already exists at $venvPath"
    Write-Host "Use -Recreate if you want to replace the existing environment."
    exit 0
}

if ((Test-Path $venvPath) -and $Recreate) {
    $backupPath = Join-Path $ProjectRoot (".venv_old_" + (Get-Date -Format "yyyy-MM-dd_HHmmss"))
    Move-Item -Path $venvPath -Destination $backupPath -Force
    Write-Host "Existing .venv moved to $backupPath"
}

$python = Resolve-PythonLauncher
Write-Host "Using Python launcher: $($python.Display)"

& $python.Executable @($python.Arguments + @("-m", "venv", $venvPath))
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create virtual environment at $venvPath"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment was created, but $venvPython was not found."
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip inside .venv"
}

if (-not $SkipRequirements) {
    & $venvPython -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install requirements from $requirementsPath"
    }
}

Write-Host "Python environment ready at $venvPath"
