# Manual weekday reminders — SP Inbound Vetting

Cursor Automation cannot run this skill end-to-end without **Gateway**,
**VixxoLink**, and **Salesforce** MCP access on the automation host. Use
**manual batch runs in Cursor** on a weekday schedule instead.

## Outlook calendar reminders (recommended)

Import the bundled recurring calendar file:

`.agents/skills/sp-inbound-vetting/reference/sp-inbound-vetting-reminders.ics`

| Reminder | Mon–Fri time | Event title |
| --- | --- | --- |
| Clock-in | **8:00 AM** (edit after import if needed) | Run SP inbound vetting (clock-in) |
| Midday | **12:00 PM** | Run SP inbound vetting (noon) |
| Afternoon | **3:00 PM** | Run SP inbound vetting (3 PM) |

Each event includes a popup alarm and the live-batch command in the description.

**Import in Outlook:** double-click the `.ics` file, or Outlook → **Add calendar**
→ **Upload from file** → select the `.ics` → save all three series.

To create reminders directly via assistant (no import), enable the **ms365** MCP
in Cursor Settings and ask the assistant to create the events with
`create-calendar-event`.

## Manual batch commands

```bash
# Live write (default when you run the skill)
python .agents/skills/sp-inbound-vetting/scripts/live_run_batch.py --queue all

# Preview only
python .agents/skills/sp-inbound-vetting/scripts/dry_run_batch.py --queue all
```

Per-queue:

```bash
python .agents/skills/sp-inbound-vetting/scripts/live_run_batch.py --queue aphelp
python .agents/skills/sp-inbound-vetting/scripts/live_run_batch.py --queue invoice-concerns
```

## Prerequisites (each manual run)

| Requirement | Purpose |
| --- | --- |
| `FRESHDESK_API_KEY` in `.env` | Freshdesk REST |
| Gateway / VixxoLink token | SP lookup (`gateway_vetting.py`) |
| `sf` CLI, org `vixxo` | Salesforce Lead/Case Tasks |
| Gateway + VixxoLink + Salesforce **MCP enabled in Cursor** | Interactive vetting in chat |

## What the batch does

1. Pull **Open**, **untouched** tickets (skip `sp-vetted` unless `--re-vet`)
2. Queues: **aphelp**, **ksonboarding**, **invoice-concerns**
3. Vet via Gateway + VixxoLink + Salesforce (fuzzy name/email match)
4. Post internal note → update `cf_sp` + tags → SF Tasks when matched

## Deprecated: Cursor Automation cron

Automated cron runs fail when the Cloud Agent lacks MCP tools for Gateway
vetting. Do not rely on `open_automation` for this skill until MCP is available
on the automation host.

## Related skills

| Skill | When to use instead |
| --- | --- |
| `sp-voicemail-triage-fast` | Subject includes `New voicemail` |
| `vixxo-spm-invoice-concerns` | Invoice resolution after `sp-vetted` |
| `vixxo-freshdesk-invoice-review` | AP Help Desk replies and classification |
