---
name: sp-inbound-vetting
description: >-
  Vets inbound service-provider identity on Salesforce queues (ksonboarding,
  COI, service.providermanagement) and Freshdesk AP Help (aphelp@vixxo.com).
  Searches Gateway and VixxoLink (SP number, SR, contact name, email, company)
  and Salesforce Lead/Case/Account. Documents findings as Salesforce Tasks on
  matched Leads/Cases (SF-primary queues) or Freshdesk internal notes + cf_sp
  (AP Help). Recommends forwarding payment/AP-style asks from SF queues to AP
  Help — draft-then-approve only. Use when vetting KS onboarding, COI, SPM,
  or AP Help intake, confirming whether an SP exists, or enriching intake with
  SP # and name. For voicemail KSOnboarding use sp-voicemail-triage. For invoice
  resolution use vixxo-spm-invoice-concerns or vixxo-freshdesk-invoice-review.
---

# SP Inbound Vetting (Salesforce + AP Help)

Work-only workflow that **vets service-provider identity** on inbound SPM mail
and cases. For each item the skill searches **Gateway** and **VixxoLink**
(SP number, SR, contact name, email, company) and **Salesforce** (Lead /
Case / Account), then **documents findings** in the system of record for that
queue.

## Intake surfaces

| Surface | System of record | Queue key | Scope |
| --- | --- | --- | --- |
| **KS Onboarding** | **Salesforce** | `ksonboarding` | Open Cases/Leads in the ksonboarding queue |
| **COI** | **Salesforce** | `coi` | Open Cases in the COI queue |
| **Service Provider Management** | **Salesforce** | `spm` | Open Cases in the service.providermanagement queue |
| **AP Help** | **Freshdesk** | `aphelp` | Open SPM tickets sent to `aphelp@vixxo.com` |

**Salesforce is the primary intake and documentation path** for ksonboarding,
COI, and service.providermanagement. **Freshdesk remains primary for AP Help**
(invoice/AP/payment intake).

Gateway and VixxoLink remain required for **SP identity resolution** on all
surfaces. Salesforce holds queue ownership, Case/Lead context, and Task notes
for the three SF-pivot queues.

This skill **enriches and annotates** intake. It does **not** classify
invoices, draft provider replies, **auto-forward** mail, or change ticket/case
status unless {{employee_name}} explicitly asks.

## Routing — SF queues vs AP Help

Some items arriving in ksonboarding, COI, or service.providermanagement are
**payment or AP-style asks** and should be **forwarded to AP Help**
(`aphelp@vixxo.com`) for processing — not handled entirely in SF vetting.

See the full routing table in [reference/queues.md](reference/queues.md).

| Ask type | Primary path | Recommended action |
| --- | --- | --- |
| COI submission, compliance, additional insured | Stay in SF (`coi`) | SF Case Task + Gateway SP lookup |
| KS onboarding, coverage, enrollment, W-9 | Stay in SF (`ksonboarding`) | SF Lead/Case Task + Gateway SP lookup |
| SPM account, sourcing, VixxoLink/trade support | Stay in SF (`spm`) | SF Case Task + Gateway SP lookup |
| Payment status, remittance, check #, invoice payment | **Forward to AP Help** | Complete SF vetting note; **recommend** forward to `aphelp@vixxo.com` |
| Invoice dispute, AP hold, billing correction | **Forward to AP Help** | Same — vet identity in SF, route AP work to Freshdesk |

**Forwarding guardrail:** Recommend forward as an **operator action** or
**internal routing note** on the SF Case. Do **not** send outbound email or
Freshdesk forwards unless {{employee_name}} explicitly approves
(draft-then-approve per workspace rules).

## When to use

- "Vet ksonboarding queue" / "vet COI queue" / "vet service.providermanagement"
- "Vet AP Help intake" / "vet aphelp tickets"
- "Check if this SP already exists" on any in-scope item
- "Enrich with SP number and name" for inbound SPM mail or SF Cases
- Batch: "vet all open ksonboarding, COI, and SPM cases" (SF SOQL)
- Batch: "vet all open aphelp items" (Freshdesk)
- Single Case: "vet Salesforce Case 00012345"
- Single ticket: "vet Freshdesk #51234"

**Use `sp-voicemail-triage`** for subject `New voicemail` items with full SF Task
writes and Outlook intake.

**Use `sp-voicemail-triage-fast`** (agent tier) to **lite-vet** KSOnboarding
voicemails after transcription — load this skill via Skills MCP
(`get_skill("sp-inbound-vetting")`) for Gateway/SF identity + routing-table reroute
before Freshdesk forward/resolve; skip SF Task writes on that path.

**Use `vixxo-spm-invoice-concerns`** for invoice/payment Gateway analysis,
proposed resolutions, and invoice workflow tags on Freshdesk Invoice Concerns.

**QSIAP voicemails (`qsiap@vixxo.com`):** use
`scripts/live_run_qsiap_voicemails.py` with routing in
[reference/qsiap-voicemail-routing.md](reference/qsiap-voicemail-routing.md):
VixxoLink support → **VINT** / type **VixxoLink Support**; payment/past-due
inquiry → **SPM** / **Invoice Support** / Open (no aphelp); invoice attachment
forward → `invoices@vixxo.com` only after Gateway confirms no invoice on SR.

**Use `vixxo-freshdesk-invoice-review`** for AP Help Desk No Agent queue,
bucket classification, and provider reply drafting.

**Use `vixxo-coi-review`** for COI certificate field compliance after identity
vetting on COI queue items.

**Use `sp-fd-sf-duplicate-bridge`** to detect Freshdesk ↔ Salesforce duplicate
pairs, scan a time window for dual-intake, or sync FD attachments to a paired SF
Case (KS onboarding mirrors, voicemail follow-up file gaps).

## Operating modes

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Batch (default)** | No single item named | Pull all in-scope open, untouched items per queue |
| **Single** | Case #, ticket id, URL, or one message | Full pipeline on one item |
| **Dry-run (opt-in)** | User says "dry-run" / "preview only" | Vetting + packet only; no writes |

**Untouched (SF):** Case/Lead not yet tagged or noted with `sp-vetted` equivalent
(see [queues.md](reference/queues.md)). **Untouched (Freshdesk):** Open and
**not** tagged `sp-vetted` (unless `re-vet`).

**Phase 1 — Vet (automatic):** intake, entity extraction, Gateway + Salesforce
search.

**Phase 2 — Document (automatic):**

| Queue type | Write path |
| --- | --- |
| SF-primary (`ksonboarding`, `coi`, `spm`) | SF Case/Lead **Task** (primary) → optional Chatter; recommend AP forward when routing table matches |
| Freshdesk-primary (`aphelp`) | Freshdesk internal note → `cf_sp` + tags → SF Lead/Case Tasks when matches found |

No separate approval step for **internal** enrichment writes —
{{employee_name}} pre-authorizes enrichment for this skill. Opt out only with
explicit **dry-run**. **Outbound forwards remain draft-then-approve.**

## Intake

Follow [reference/intake.md](reference/intake.md) and
[reference/queues.md](reference/queues.md).

**In scope (batch default — `all`):**

1. Open Cases (and related Leads where applicable) in SF queues
   `ksonboarding`, `coi`, `spm` — via SOQL in [queues.md](reference/queues.md).
2. Open SPM Freshdesk tickets (`group_id:159000485013`, `status:2`) sent to
   `aphelp@vixxo.com` (recipient gate).

**Out of scope (default):** items already marked vetted; subject includes
`New voicemail` (unless user says include voicemails).

## Output format

### Batch summary (top of every batch run)

See [reference/examples.md](reference/examples.md).

### Vetting packet (per item)

```markdown
## SP Inbound Vetting — {SF Case # or Freshdesk #}

| Field | Value |
| --- | --- |
| **Source** | SF Case {CaseNumber} / Freshdesk #{id} |
| **Queue** | ksonboarding / coi / spm / aphelp |
| **System of record** | Salesforce / Freshdesk |
| **Requester** | {name} <{email}> |
| **Contact name** | {from Case contact or FD requester} |
| **Company** | {extracted or Not stated} |
| **Reference IDs** | {SP # / SR / invoice / none} |
| **Entity posture** | {from company vetting} |
| **Gateway SP** | {SP # — name or No match} |
| **Salesforce** | {Lead / Case / Account ids or None} |
| **Routing** | Stay in SF / Recommend forward to AP Help |
| **cf_sp target** | {value — Freshdesk only} |
| **Confidence** | High / Medium / Low |

### Company vetting
{table from reference/company-vetting.md}

### Summary / open questions
…

### Actions taken
- **SF Case/Lead Task:** {Id + posted | N/A | failed}
- **Internal note (FD):** {posted | N/A | failed}
- **cf_sp + tags (FD):** {updated | N/A | skipped}
- **Recommended forward:** {aphelp@vixxo.com — draft for approval | none}
```

## Workflow (per item)

1. **Acquire content** — SF Case/Lead fields + email thread; or `get_ticket`,
   conversations, requester for AP Help; optional Outlook when no ticket/Case.
2. **Classify routing** — Apply [queues.md](reference/queues.md) routing table.
   Flag **Recommend forward to AP Help** when payment/AP signals dominate.
3. **Extract entities** — company, SP #, SR, contact email/phone
   ([intake.md](reference/intake.md)). Parse **email signature** company names
   before generic mailbox labels.
4. **Company vetting** — [reference/company-vetting.md](reference/company-vetting.md):
   Gateway (contact + company → SP #), VixxoLink SR cross-check, Salesforce
   Lead/Case/Account SOQL.
5. **Document (SF-primary queues):**
   - Post **Task** on matched Case (required when vetting an open queue Case).
   - Post **Task** on matched Lead when Lead found.
   - Include routing recommendation (stay vs forward to AP Help) in Task body.
   - Do **not** auto-forward — surface draft forward language for operator approval.
6. **Document (AP Help — Freshdesk):**
   - Post Freshdesk internal note —
     [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md).
   - Update `cf_sp` + `sp-vetted` tags when posture known.
   - Post SF Lead/Case Tasks when matches found.
7. **Record failures** in batch summary; continue where safe.

## Batch scripts

**Primary path:** Gateway, VixxoLink, and Salesforce lookups run through **Cursor
MCP** in an agent session (`project-0-assistant-CGagner-gateway`,
`project-0-assistant-CGagner-vixxolink`, `project-0-assistant-CGagner-salesforce`).
No file token is required when those MCPs are enabled.

Batch shell scripts use `mcp_http.py`, which does **not** inherit Cursor OAuth.
For unattended shell runs, enrich dry-run JSON with MCP results from an
interactive session, then apply with `live_run_batch.py --data`.

| Command | Purpose |
| --- | --- |
| `python scripts/dry_run_batch.py --queue aphelp` | Preview AP Help vetting (Gateway may be empty in shell) |
| `python scripts/live_run_batch.py --data .tmp/gateway-mcp-revet-*.json` | Apply MCP-enriched vetting writes |
| `python scripts/live_run_batch.py --queue aphelp` | Live vet + write AP Help |
| SF queues `ksonboarding`, `coi`, `spm` | Run via Salesforce MCP SOQL + agent workflow (no batch script yet) |

Legacy `--queue ksonboarding` / `--queue invoice-concerns` Freshdesk pulls
remain in scripts during transition; prefer SF SOQL for ksonboarding. Invoice
Concerns vetting on Freshdesk is owned by sibling skills — see [queues.md](reference/queues.md).

## Document checklist (automatic)

```
Vetting progress — {Case or ticket id}:
- [ ] Routing classified (stay SF vs recommend AP Help forward)
- [ ] Gateway SP search complete (KS/SR/email/name/company)
- [ ] VixxoLink SR cross-check complete (when SR present)
- [ ] Salesforce Lead search complete (company + contact name + email)
- [ ] Salesforce Case search complete
- [ ] SF Case/Lead Task posted (SF-primary queues)
- [ ] Internal note posted (AP Help / when FD ticket exists)
- [ ] cf_sp + sp-vetted tag updated (AP Help only)
- [ ] Forward recommendation drafted (when routing table matches — no auto-send)
```

## Guardrails

- Work context only — Vixxo SP operations.
- Facts from Case/ticket content and MCP responses; mark assumptions.
- **No outbound email** — no `forward_ticket`, `forward-mail-message`, Case
  email actions, or public replies unless {{employee_name}} explicitly directs it.
- **Recommended AP Help forwards** are internal notes / draft language only.
- **No Case/ticket close / resolve** from this skill by default.
- Never invent SP numbers or Salesforce ids — use Gateway/SOQL results only.
- Redact full phone numbers in chat summaries; keep full numbers in internal
  notes for operators.

## Additional resources

| File | Purpose |
| --- | --- |
| [reference/intake.md](reference/intake.md) | SF + Freshdesk queue pull + entity extraction |
| [reference/queues.md](reference/queues.md) | Queue registry, SOQL filters, routing table |
| [reference/company-vetting.md](reference/company-vetting.md) | Gateway + Salesforce search |
| [reference/freshdesk-note-template.md](reference/freshdesk-note-template.md) | AP Help internal note body |
| [reference/salesforce-notes.md](reference/salesforce-notes.md) | Task / Chatter writes (SF-primary) |
| [reference/troubleshooting.md](reference/troubleshooting.md) | Known failure modes + fixes |
| [reference/qsiap-voicemail-routing.md](reference/qsiap-voicemail-routing.md) | QSIAP/SPM voicemail routing (VINT, payment, invoice forward) |

Sibling skills: **`sp-voicemail-triage`** (voicemail routing),
**`vixxo-coi-review`** (COI certificate compliance),
**`vixxo-spm-invoice-concerns`** (invoice concern resolution),
**`vixxo-freshdesk-invoice-review`** (AP Help Desk invoice triage).
