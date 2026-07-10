# Safa Style — deploy from your PC to the DigitalOcean droplet.
#
# First time:
#   1. Copy deploy.config.example to deploy.config
#   2. Push code to GitHub
#   3. SSH into the droplet once and run setup (see README)
#
# Every update:
#   git add . && git commit -m "..." && git push
#   .\deploy.ps1

param(
    [switch]$Setup,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $Root "deploy.config"

if (-not (Test-Path $ConfigFile)) {
    Write-Host "Missing deploy.config — copy deploy.config.example and set DROPLET_IP + SSH_USER." -ForegroundColor Yellow
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

Write-Host "Connecting to $target ..." -ForegroundColor Cyan

if ($Setup) {
    Write-Host "Running one-time server setup (this takes a few minutes)..." -ForegroundColor Cyan
    ssh $target "bash -s" < (Join-Path $Root "deploy\setup-server.sh")
    exit $LASTEXITCODE
}

if ($Status) {
    ssh $target "systemctl status gunicorn-safastyle --no-pager; echo '---'; curl -sI http://127.0.0.1/ | head -5"
    exit $LASTEXITCODE
}

# Normal deploy: push should already be on GitHub; server pulls and restarts.
Write-Host "Deploying latest main branch..." -ForegroundColor Cyan
ssh $target "cd /var/www/safastyle && bash deploy/deploy.sh"
exit $LASTEXITCODE
