param(
  [Parameter(Mandatory)][string]$RunnerDirectory,
  [Parameter(Mandatory)][switch]$DedicatedEnvironmentConfirmed
)
$ErrorActionPreference = 'Stop'
if (-not $DedicatedEnvironmentConfirmed) { throw 'Use a disposable dedicated Windows x64 environment without personal files or credentials.' }
if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Windows x64 required' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run from a standard account, not an elevated shell' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI authenticated to the private repository is required; do not put PATs in this script' }
$visibility = gh api repos/gsh4124-cyber/hwangje-vault --jq .visibility
if ($LASTEXITCODE -ne 0 -or $visibility -ne 'private') { throw 'Private repository access verification failed' }
$target = [IO.Path]::GetFullPath($RunnerDirectory)
if (Test-Path -LiteralPath $target) { throw 'Use a new empty dedicated runner directory' }
New-Item -ItemType Directory -Path $target | Out-Null
$zip = Join-Path $target 'runner.zip'
Invoke-WebRequest -Uri 'https://github.com/actions/runner/releases/download/v2.338.0/actions-runner-win-x64-2.338.0.zip' -OutFile $zip
if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'f48e0750a21812bca5f82de5f7f5aeae71abee647fab5a582f1742d07eba455f') { throw 'Official runner SHA256 mismatch' }
Expand-Archive -LiteralPath $zip -DestinationPath $target
Write-Host 'Official runner extracted and verified. No registration, service, startup task, or execution performed.'
Write-Host ('Next, in the dedicated environment: Set-Location -LiteralPath ' + "'" + $target + "'")
Write-Host 'Obtain a one-hour registration token from repository Settings > Actions > Runners > New self-hosted runner.'
Write-Host '$registration = Read-Host "Registration token" -AsSecureString'
Write-Host '$plain = [Net.NetworkCredential]::new("", $registration).Password'
Write-Host '.\config.cmd --url https://github.com/gsh4124-cyber/hwangje-vault --token $plain --name vault-windows-qa --labels hwangje-vault-qa --work _work --ephemeral --unattended'
Write-Host 'Remove-Variable plain,registration'
Write-Host '.\run.cmd'
Write-Host 'Use only a reviewed workflow_dispatch on main with [self-hosted, Windows, X64, hwangje-vault-qa]. Dispose of the environment after one job; retain redacted diagnostics.'
