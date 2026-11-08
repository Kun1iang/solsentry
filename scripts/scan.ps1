Param(
    [string]$Path = "examples/vulnerable",
    [string]$Format = "console",
    [string]$Output = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $root "src"
Set-Location $root

$argsList = @("scan", $Path, "--format", $Format)
if ($Output) {
    $argsList += @("--output", $Output)
}
& python -m solsentry @argsList
exit $LASTEXITCODE
