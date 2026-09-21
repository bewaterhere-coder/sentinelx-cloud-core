param([string]$TaskName = "DevForgeUserGitBroker")
$ErrorActionPreference = "Stop"
Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Output "Removed Scheduled Task $TaskName. Broker files were preserved."
