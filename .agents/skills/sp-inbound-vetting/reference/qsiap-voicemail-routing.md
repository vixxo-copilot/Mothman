# QSIAP / SPM voicemail and email intake routing

## Voicemail routing (qsiap `@vixxo.com`)

Script: `sp-inbound-vetting/scripts/live_run_qsiap_voicemails.py`  
Logic: `voicemail_intake_routing.py`

**Vetting order:** transcribe `.wav` attachment first (when present), then route
from spoken content + attachment filenames. Caller ID and callback phone often
belong to **technician cell lines** not indexed in SF/Gateway — use transcript
company names (`"this is … with {company}"`) and operator IDs when phone lookup
returns Unknown.

**Duplicate merge:** always merge into an **Open** primary (`status=2`). Never
use Resolved/Closed as primary. Helper: `sp-inbound-vetting/scripts/qsiap_merge.py`
(`pick_open_merge_primary`, `merge_qsiap_tickets`). Pending-only groups may be
reopened to Open before merge.

| Ask | Group | Type | Status | Forward |
| --- | --- | --- | --- | --- |
| **VixxoLink support** (portal, login, password, account setup, explicit “VixxoLink support”) | **VINT** `159000486559` | **VixxoLink Support** | Open | **No** |
| **Payment status / past-due inquiry** | **SPM** `159000485013` | **Invoice Support** | Open | **No aphelp** |
| **Invoice attachment + submit ask** | SPM | Invoice Support | Open | **`invoices@vixxo.com` only after Gateway vet** confirms no invoice on SR |
| Gateway shows invoice already on SR | SPM | Invoice Support | Open | **No** — note `invoice-on-sr` |

Gateway check uses `gateway_sr_invoice_status()` / SR invoice list before recommending AP forward.

## Email routing (SPM invoice concerns)

Same priority order in `vixxo-spm-invoice-concerns/scripts/spm_classifier.py`:

1. VixxoLink portal/support → VINT / VixxoLink Support  
2. Payment/past-due → SPM / Invoice Support / Open  
3. Invoice intake forward only with real invoice attachments and Gateway clearance  

Clear-hold runs must **not** force `invoice-intake-forward` for portal or payment inquiries (audit FD **#70128**).

## Outbound guardrail

`invoices@vixxo.com` forward remains **operator-approved** unless {{employee_name}} explicitly directs execute. Routing notes record forward candidates only.
