param(
  [string]$TaskName = "DevForgeUserGitBroker",
  [string]$BrokerDir = $PSScriptRoot,
  [string]$PythonwPath = "C:\ProgramData\SentinelX\.venv\Scripts\pythonw.exe"
)
$ErrorActionPreference = "Stop"

$interactiveUser = (Get-CimInstance Win32_ComputerSystem).UserName
if (-not $interactiveUser) { throw "No interactive Windows user is logged on." }

$pythonw = $PythonwPath
$broker = Join-Path $BrokerDir "broker.py"
if (-not (Test-Path $pythonw)) { throw "SentinelX pythonw not found: $pythonw" }
if (-not (Test-Path $broker)) { throw "Broker script not found: $broker" }
if (-not (Test-Path (Join-Path $BrokerDir "broker-config.json"))) {
  throw "broker-config.json is required. Copy broker-config.example.json and set operator-approved allowed_roots first."
}

New-Item -ItemType Directory -Force -Path (Join-Path $BrokerDir "runtime\requests") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $BrokerDir "runtime\results") | Out-Null

$taskArgs = '"' + $broker + '" --serve'
$action = New-ScheduledTaskAction -Execute $pythonw -Argument $taskArgs -WorkingDirectory $BrokerDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $interactiveUser
$principal = New-ScheduledTaskPrincipal -UserId $interactiveUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 720 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300
Start-ScheduledTask -TaskName $TaskName

$ready = Join-Path $BrokerDir "runtime\broker-ready.json"
$deadline = (Get-Date).AddSeconds(15)
while ((Get-Date) -lt $deadline) {
  if (Test-Path $ready) {
    try {
      $data = Get-Content $ready -Raw | ConvertFrom-Json
      if ($data.ready -eq $true) { break }
    } catch {}
  }
  Start-Sleep -Milliseconds 250
}
if (-not (Test-Path $ready)) { throw "Broker task registered, but readiness file did not appear." }

$task = Get-ScheduledTask -TaskName $TaskName
[pscustomobject]@{
  TaskName = $TaskName
  State = $task.State
  InteractiveUser = $interactiveUser
  RunLevel = "Limited"
  Broker = $broker
  ReadyFile = $ready
}
