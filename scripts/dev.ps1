# Prepara el entorno local de desarrollo (Windows / PowerShell) y ejecuta las pruebas.
#   .\scripts\dev.ps1            -> instala dependencias, genera fixtures y corre pytest
#   .\scripts\dev.ps1 -SinTests  -> solo prepara el entorno
param([switch]$SinTests)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Se creo .env a partir de .env.example; ajusta las credenciales."
}

python tests/fixtures/generate_pdfs.py

if (-not $SinTests) {
    pytest
}
