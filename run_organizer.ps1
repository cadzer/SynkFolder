param(
    [switch]$Watch = $true,
    [switch]$Once = $false
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return "py"
            }
        } catch {}
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            & python --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return "python"
            }
        } catch {}
    }
    return $null
}

function Install-PythonIfMissing {
    $pythonCmd = Get-PythonCommand
    if ($pythonCmd) {
        Write-Host "Python found: $pythonCmd"
        return $pythonCmd
    }

    Write-Step "Python not found. Installing Python 3 via winget"

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is not available on this PC. Install App Installer from Microsoft Store, then run again."
    }

    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements | Out-Host

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    $pythonCmd = Get-PythonCommand
    if (-not $pythonCmd) {
        throw "Python install command finished, but Python is still not on PATH. Restart terminal and run script again."
    }

    Write-Host "Python installed successfully: $pythonCmd"
    return $pythonCmd
}

Write-Step "Checking Python"
$python = Install-PythonIfMissing

Write-Step "Installing dependencies"
& $python -m pip install --upgrade pip
& $python -m pip install -r "requirements.txt"

Write-Step "Starting SynkFolder"
if ($Once) {
    & $python "main.py" --once
} elseif ($Watch) {
    & $python "main.py" --watch
} else {
    & $python "main.py" --once
}
