$thisfolder = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath('.\')
Set-Location $thisfolder
$mypy = ".\envo\Scripts\python.exe"

# $action = New-ScheduledTaskAction -Execute 'Powershell.exe' -Argument

$PSScriptRoot
$thisfolder
$mypy
Start-sleep -Seconds 10