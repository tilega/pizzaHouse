$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$entry = Join-Path $project 'pizzaHouse.py'
if (-not (Test-Path -LiteralPath $entry)) { throw 'pizzaHouse.py was not found in the installer folder.' }
$pythonExe = (& py -3.13 -c 'import sys; print(sys.executable)' | Select-Object -First 1)
if ($LASTEXITCODE -ne 0 -or -not $pythonExe -or -not (Test-Path -LiteralPath $pythonExe)) { throw 'Python 3.13 could not be found using py -3.13.' }
$pythonw = Join-Path (Split-Path $pythonExe -Parent) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { throw 'pythonw.exe was not found next to python.exe.' }
$desktop = [Environment]::GetFolderPath('Desktop')
if (-not $desktop) { throw 'Windows desktop folder was not found.' }
$linkPath = Join-Path $desktop 'Pizza House.lnk'
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($linkPath)
$link.TargetPath = $pythonw
$link.Arguments = '"' + $entry + '"'
$link.WorkingDirectory = $project
$icon = Join-Path $project 'pizza_house.ico'
if (Test-Path -LiteralPath $icon) { $link.IconLocation = $icon }
$link.Description = 'Pizza House application'
$link.WindowStyle = 1
$link.Save()
Write-Host ('Shortcut created: ' + $linkPath)
