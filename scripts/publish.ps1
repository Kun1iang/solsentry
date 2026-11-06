# Publish SolSentry to a remote Git host.
#
# Usage:
#   1. Create an EMPTY repository on GitHub/Gitee (no README, no .gitignore).
#   2. Run:
#        .\scripts\publish.ps1 -RemoteUrl "git@github.com:<you>/solsentry.git"
#   3. The script pushes main, develop, and all version tags.

param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".git")) {
    throw "当前目录不是 Git 仓库。"
}

$existing = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0 -and $existing) {
    Write-Host "origin 已存在: $existing" -ForegroundColor Yellow
    $answer = Read-Host "是否替换为 $RemoteUrl ? (y/N)"
    if ($answer -ne "y") { exit 1 }
    git remote set-url origin $RemoteUrl
} else {
    git remote add origin $RemoteUrl
}

Write-Host "`n== Push branches ==" -ForegroundColor Cyan
git push -u origin main
git push -u origin develop

Write-Host "`n== Push tags ==" -ForegroundColor Cyan
git push origin --tags

Write-Host "`n完成。打开远程仓库，确认 README、LICENSE、Actions 与分支保护设置。" -ForegroundColor Green
Write-Host "建议开启：main 分支保护、要求 PR + CI、禁止 force push。" -ForegroundColor Green
