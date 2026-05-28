param(
    [string]$Version = "1.0.0"
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
            if ($LASTEXITCODE -eq 0) { return "py" }
        } catch {}
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            & python --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return "python" }
        } catch {}
    }
    return $null
}

function Ensure-Python {
    $python = Get-PythonCommand
    if ($python) { return $python }

    Write-Step "Installing Python with winget"
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is required to auto-install Python."
    }
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements | Out-Host

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    $python = Get-PythonCommand
    if (-not $python) { throw "Python was installed but is not on PATH yet. Restart terminal and retry." }
    return $python
}

function Ensure-InnoSetup {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }

    Write-Step "Installing Inno Setup with winget"
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is required to auto-install Inno Setup."
    }
    winget install -e --id JRSoftware.InnoSetup --accept-source-agreements --accept-package-agreements | Out-Host

    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }

    throw "Inno Setup install finished but ISCC.exe was not found at expected path."
}

Write-Step "Preparing build environment"
$python = Ensure-Python
& $python -m pip install --upgrade pip
& $python -m pip install -r "requirements.txt"
& $python -m pip install pyinstaller

Write-Step "Cleaning previous build artifacts"
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "dist_installer") { Remove-Item -Recurse -Force "dist_installer" }

if (-not (Test-Path "assets\SynkFolder.png")) {
    throw "Missing assets\SynkFolder.png. Place SynkFolder.png in the assets folder."
}
if (-not (Test-Path "assets\SynkFolder.ico")) {
    Write-Step "Generating ICO from PNG"
    & $python -c "from PIL import Image; img=Image.open('assets/SynkFolder.png').convert('RGBA'); img.save('assets/SynkFolder.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
}

Write-Step "Building standalone app executable"
& $python -m PyInstaller `
    --noconfirm `
    --onefile `
    --noconsole `
    --name "SynkFolder" `
    --icon "assets\SynkFolder.ico" `
    --add-data "config.json;." `
    --add-data "assets\SynkFolder.png;assets" `
    --add-data "assets\SynkFolder.ico;assets" `
    "app_launcher.py"

if (-not (Test-Path "dist\SynkFolder.exe")) {
    throw "PyInstaller did not produce dist\SynkFolder.exe"
}

Write-Step "Building Windows installer (.exe)"
$iscc = Ensure-InnoSetup
& $iscc "/DMyAppVersion=$Version" "SynkFolder.iss"

Write-Step "Done"
Write-Host "Installer created in: .\dist_installer" -ForegroundColor Green
