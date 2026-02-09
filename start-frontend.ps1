# Start frontend dev server. Run from project root: .\start-frontend.ps1
$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }
Set-Location (Join-Path $root "frontend")
npm run dev
