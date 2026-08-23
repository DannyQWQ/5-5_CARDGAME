$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$frontendRoot = Join-Path $projectRoot 'frontend'
$pythonCommand = Get-Command python -ErrorAction Stop
$pnpmCommand = Get-Command pnpm -ErrorAction SilentlyContinue

if (-not $pnpmCommand) {
    $bundledNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin'
    $bundledPnpm = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd'
    if (-not (Test-Path -LiteralPath $bundledPnpm)) {
        throw 'pnpm was not found. Install Node.js and pnpm before starting the web UI.'
    }
    $env:Path = "$bundledNode;$env:Path"
    $pnpmPath = $bundledPnpm
} else {
    $pnpmPath = $pnpmCommand.Source
}

$apiProcess = Start-Process -FilePath $pythonCommand.Source -ArgumentList 'web_api.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
try {
    Write-Host 'Five by Five is starting at http://localhost:3000/'
    & $pnpmPath --dir $frontendRoot dev
} finally {
    if (-not $apiProcess.HasExited) {
        Stop-Process -Id $apiProcess.Id
    }
}

