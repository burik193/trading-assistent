# Start backend with .env loaded from project root.
# Run from project root: .\start-backend.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }
$env:PYTHONPATH = Join-Path $root "backend"
# Load .env into environment
if (Test-Path (Join-Path $root ".env")) {
    Get-Content (Join-Path $root ".env") | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$' -and $_ -notmatch '^\s*#') {
            $name = $matches[1]
            $value = $matches[2].Trim().Trim('"').Trim("'")
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}
Set-Location (Join-Path $root "backend")
& (Join-Path $root ".venv\Scripts\uvicorn.exe") main:app --reload --host 0.0.0.0 --port 8000
