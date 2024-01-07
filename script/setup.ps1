#Requires -Version 7.0
# Setups the repository.

$ErrorActionPreference = 'Stop'

Set-Location -Path "$PSScriptRoot/.."

$SettingsFile = "./.vscode/settings.json"
$SettingsTemplateFile = "./.vscode/settings.default.json"

if ((Test-Path $SettingsFile) -eq $false) {
    Write-Output "Copy $SettingsTemplateFile to $SettingsFile."
    Copy-Item $SettingsTemplateFile $SettingsFile
}

New-Item config -ItemType Directory -ErrorAction SilentlyContinue | Out-Null

if (($null -eq $Env:DEVCONTAINER) -and ($null -eq $Env:VIRTUAL_ENV)) {
    python3 -m venv venv
    if (Test-Path ./venv/bin) {
        . ./venv/bin/Activate.ps1
    }
    else {
        . ./venv/Scripts/Activate.ps1
    }
}
# virtualenv on Windows doesn't generate a "python3.exe", so we need to copy the python.exe, else we would run everything outside the venv
if ((Test-Path $Env:VIRTUAL_ENV/Scripts) -and -not (Test-Path $Env:VIRTUAL_ENV/Scripts/python3.exe)) {
    Copy-Item $Env:VIRTUAL_ENV/Scripts/python.exe $Env:VIRTUAL_ENV/Scripts/python3.exe
}

. ./script/bootstrap.ps1

pre-commit install
python3 -m pip install -e . --config-settings editable_mode=compat --constraint homeassistant/package_constraints.txt
python3 -m script.translations develop --all

hass --script ensure_config -c config

if (-not (Select-String "logger" ./config/configuration.yaml)) {
    Add-Content ./config/configuration.yaml -Value @"
logger:
  default: info
  logs:
    homeassistant.components.cloud: debug
"@
}
