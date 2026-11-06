$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $root "src"
$env:PYTHONIOENCODING = "utf-8"
Set-Location $root

Write-Host "== Compile ==" -ForegroundColor Cyan
python -m compileall -q src

Write-Host "`n== Tests ==" -ForegroundColor Cyan
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$out = Join-Path $root "docs\assets\generated"
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host "`n== Console report ==" -ForegroundColor Cyan
python -m solsentry scan examples/vulnerable --color never

Write-Host "`n== Generate HTML / JSON / SARIF / Markdown ==" -ForegroundColor Cyan
python -m solsentry scan examples/vulnerable --format html --output (Join-Path $out "scan-report.html") --quiet
python -m solsentry scan examples/vulnerable --format json --output (Join-Path $out "scan-report.json") --quiet
python -m solsentry scan examples/vulnerable --format sarif --output (Join-Path $out "scan-report.sarif") --quiet
python -m solsentry scan examples/vulnerable --format markdown --output (Join-Path $out "scan-report.md") --quiet

Write-Host "`nArtifacts:" -ForegroundColor Green
Get-ChildItem $out | Select-Object Name, Length | Format-Table -AutoSize
