# Safa Style - deploy from your PC to the DigitalOcean droplet.
#
# Every update:
#   .\deploy.bat
#   or: .\deploy.ps1 -Push

param(
    [switch]$Setup,
    [switch]$Status,
    [switch]$Push,
    [string]$Message = "Deploy update"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $Root "deploy.config"

if (-not (Test-Path $ConfigFile)) {
    Write-Host "Missing deploy.config - copy deploy.config.example and set DROPLET_IP + SSH_USER." -ForegroundColor Yellow
    exit 1
}

$config = @{}
Get-Content $ConfigFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        $config[$matches[1].Trim()] = $matches[2].Trim()
    }
}

$ip = $config["DROPLET_IP"]
$user = $config["SSH_USER"]
$target = "${user}@${ip}"

if (-not $ip -or -not $user) {
    Write-Host "deploy.config must set DROPLET_IP and SSH_USER." -ForegroundColor Red
    exit 1
}

$sshArgs = @("-o", "ConnectTimeout=15")
Write-Host "Connecting to $target ..." -ForegroundColor Cyan

if ($Setup) {
    Write-Host "Running one-time server setup..." -ForegroundColor Cyan
    Get-Content (Join-Path $Root "deploy\setup-server.sh") | ssh @sshArgs $target "bash -s"
    exit $LASTEXITCODE
}

if ($Status) {
    ssh @sshArgs $target "systemctl status gunicorn-safastyle --no-pager; echo '---'; curl -sI https://safastyle.com/ | head -5"
    exit $LASTEXITCODE
}

if ($Push) {
    Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
    git add -A
    $dirty = git status --porcelain
    if ($dirty) {
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } else {
        Write-Host "No local changes to commit." -ForegroundColor DarkGray
    }
    git push origin main
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Deploying latest main branch..." -ForegroundColor Cyan
ssh @sshArgs $target "bash -lc 'cd /var/www/safastyle && bash deploy/deploy.sh'"
exit $LASTEXITCODE
