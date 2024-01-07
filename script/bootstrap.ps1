#Requires -Version 7.0
# Resolve all dependencies that the application requires to run.

# Stop on errors
$ErrorActionPreference = 'Stop'

Set-Location "$PSScriptRoot/.."

Write-Output "Installing development dependencies..."
python3 -m pip install wheel --constraint homeassistant/package_constraints.txt --upgrade
python3 -m pip install colorlog pre-commit (select-String awesomeversion requirements.txt -raw) --constraint homeassistant/package_constraints.txt --upgrade
python3 -m pip install -r requirements_test.txt -c homeassistant/package_constraints.txt --upgrade
