# 1. enter this folder
## if tasks are not scheduled
# 2. schedule all tasks in .\routine
## else
# 3. unschedule all tasks
$task = "getGpuPrices"
Set-Location $PSScriptRoot

$action = New-ScheduledTaskAction -Execute 'Powershell.exe' -Argument .\hide_caller.vbs
$trigger = New-ScheduledTaskTrigger -Daily -AtStartup -DaysInterval 3
if(Get-ScheduledTask $task -ErrorAction Ignore) {
    Unregister-ScheduledTask -TaskName $task
} else {
    Register-ScheduledTask -Action $action -Trigger $trigger -TaskName $task -Description "Tarefa de coleta de preços do Price_indexr"
}
