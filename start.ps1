Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Test-PythonCommand {
  param([string[]]$Command)
  try {
    $version = & $Command[0] $Command[1..($Command.Length - 1)] -c "import sys; print(sys.version_info[0])" 2>$null
    return ($LASTEXITCODE -eq 0 -and "$version".Trim().StartsWith("3"))
  } catch {
    return $false
  }
}

$candidates = @(
  @("py", "-3"),
  @("py"),
  @("python"),
  @("python3")
)

foreach ($cmd in $candidates) {
  if (Test-PythonCommand -Command $cmd) {
    & $cmd[0] $cmd[1..($cmd.Length - 1)] "server.py" @args
    exit $LASTEXITCODE
  }
}

Write-Host ""
Write-Host "Python 3 was not found on this PC."
Write-Host ""
Write-Host "Install Python from https://www.python.org/downloads/"
Write-Host "During setup, check `"Add python.exe to PATH`"."
Write-Host "Then open a NEW PowerShell window and run:"
Write-Host "  py server.py"
Write-Host ""
Write-Host "If Windows opens the Microsoft Store for python/python3, disable those"
Write-Host "App execution aliases:"
Write-Host "  Settings > Apps > Advanced app settings > App execution aliases"
Write-Host ""
exit 1
