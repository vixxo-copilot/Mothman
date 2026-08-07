#Requires -Version 5.1
<#
.SYNOPSIS
  Weekday voicemail triage tick for Task Scheduler (Outlook batch + wake marker).

.DESCRIPTION
  Runs locally without a Cursor agent session. Intended for Mon-Fri every 2 hours.
  - Outlook VM folder: batch_process_outlook.py --since-last-batch
  - Writes tick log + AGENT_LOOP_TICK marker under .tmp/scheduler-ticks/
  - SF 4046 Case Task writes still need an agent/Cursor session (see SKILL.md)

  Exit 0 on success; non-zero if Outlook batch fails.
#>
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
Set-Location $RepoRoot

$dow = (Get-Date).DayOfWeek
if ($dow -eq [DayOfWeek]::Saturday -or $dow -eq [DayOfWeek]::Sunday) {
    Write-Output "SKIP weekend=$dow"
    exit 0
}

$stamp = Get-Date -Format "yyyyMMddTHHmmssZ"
$logDir = Join-Path $RepoRoot ".agents\skills\sp-voicemail-triage\.tmp\scheduler-ticks"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "tick-$stamp.log"

function Write-Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "o"), $msg
    Add-Content -Path $logFile -Value $line
    Write-Output $line
}

Write-Log "START voicemail triage tick repo=$RepoRoot"

$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Write-Log "ERROR python not on PATH"
    exit 2
}
$python = $pyCmd.Source

$outlookScript = Join-Path $RepoRoot ".agents\skills\sp-voicemail-triage\scripts\batch_process_outlook.py"
Write-Log "RUN Outlook batch"
$outlookRc = 1
try {
    & $python $outlookScript --since-last-batch *>&1 | Tee-Object -FilePath $logFile -Append
    $outlookRc = $LASTEXITCODE
} catch {
    Write-Log "ERROR Outlook batch: $_"
    exit 3
}
Write-Log "Outlook exit=$outlookRc"

$marker = Join-Path $logDir "AGENT_LOOP_TICK_voicemail_triage.latest.txt"
@(
    "AGENT_LOOP_TICK_voicemail_triage"
    "time=$stamp"
    "prompt=Run sp-voicemail-triage locally: Salesforce 4046 Vendor Relations Cases (open, New voicemail) + QSIAP + Outlook VM. Do NOT scan FD KSOnboarding. Billing/Payment FD-only on QSIAP; close AP on SF 4046 as Duplicate."
    "outlook_exit=$outlookRc"
    "log=$logFile"
) | Set-Content -Path $marker -Encoding UTF8
Write-Log "WROTE marker $marker"
Write-Log "DONE"

if ($outlookRc -eq 0) { exit 0 } else { exit $outlookRc }
