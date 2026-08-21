#Requires -Version 5.1
<#
.SYNOPSIS
  Install (or replace) the weekday 2-hour Mothman voicemail triage Scheduled Task.

.DESCRIPTION
  Task name: MothmanVoicemailTriage
  Schedule: every 2 hours, Monday-Friday, starting 07:00 local (12h repetition window)
  Action: run_voicemail_triage_tick.ps1 (Outlook batch + tick marker)

  Uninstall: .\install_voicemail_triage_task.ps1 -Uninstall
#>
param(
    [switch]$Uninstall,
    [string]$TaskName = "MothmanVoicemailTriage"
)

$ErrorActionPreference = "Stop"
$tickScript = Join-Path $PSScriptRoot "run_voicemail_triage_tick.ps1"
if (-not (Test-Path $tickScript)) {
    throw "Missing tick script: $tickScript"
}

function Remove-TaskQuiet([string]$name) {
    cmd /c "schtasks /Delete /TN `"$name`" /F >NUL 2>&1" | Out-Null
}

if ($Uninstall) {
    Remove-TaskQuiet $TaskName
    Write-Output "Removed scheduled task '$TaskName' (if it existed)."
    exit 0
}

$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$tickScript`""
# schtasks: weekly Mon-Fri at 07:00, repeat every 2 hours for 12 hours
Remove-TaskQuiet $TaskName
$tr = "powershell.exe $arg"
$createOut = cmd /c "schtasks /Create /TN `"$TaskName`" /TR `"$tr`" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 07:00 /RI 120 /DU 12:00 /RL LIMITED /F"
if ($LASTEXITCODE -ne 0) {
    throw "schtasks /Create failed ($LASTEXITCODE): $createOut"
}

schtasks.exe /Query /TN $TaskName /V /FO LIST | Select-String -Pattern "TaskName|Status|Next Run|Last Run|Task To Run|Repeat|Start Time|Days"
Write-Output ""
Write-Output "Installed '$TaskName'."
Write-Output "Tick script: $tickScript"
Write-Output "Note: Outlook batch runs unattended; SF 4046 Case Tasks still need a Cursor agent pass."
