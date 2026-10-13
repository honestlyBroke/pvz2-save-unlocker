# One-click: pull PvZ2 save from the phone over USB, unlock every plant, push it back.
# Usage: powershell -ExecutionPolicy Bypass -File unlock_plants.ps1 [--shop-only]
$ErrorActionPreference = 'Stop'
$pkg = 'com.ea.game.pvz2_row'
$here = $PSScriptRoot

$adb = (Get-Command adb -ErrorAction SilentlyContinue).Source
if (-not $adb) { $adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" }
if (-not (Test-Path $adb)) { throw 'adb not found. Install Android platform-tools.' }

$devices = & $adb devices | Select-String "`tdevice$"
if (-not $devices) { throw 'No phone found. Plug it in, enable USB debugging, accept the prompt on the phone.' }

& $adb shell am force-stop $pkg
$remote = (& $adb shell "find /sdcard/Android/data/$pkg -name pp.dat 2>/dev/null" | Select-Object -First 1)
if (-not $remote) { throw "pp.dat not found under /sdcard/Android/data/$pkg. Launch the game once, finish the intro, then retry." }
$remote = $remote.Trim()
Write-Host "Save: $remote"

$work = Join-Path $here ("save_backups\" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force $work | Out-Null
$local = Join-Path $work 'pp.dat'
& $adb pull $remote $local
if ($LASTEXITCODE) { throw 'adb pull failed' }

python (Join-Path $here 'pvz2_unlock_plants.py') $local @args
if ($LASTEXITCODE) { throw 'Unlock failed; phone save untouched.' }

& $adb push $local $remote
if ($LASTEXITCODE) { throw 'adb push failed; phone save untouched.' }
Write-Host "Done. Original kept at $local.bak. Start the game with internet OFF the first time."
