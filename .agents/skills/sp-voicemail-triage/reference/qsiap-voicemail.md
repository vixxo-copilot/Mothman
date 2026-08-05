# QSIAP AP Voicemails

Third default batch source for **`sp-voicemail-triage`**: open Freshdesk SPM
tickets routed to **`qsiap@vixxo.com`** with subject **`New voicemail`**.

## Intake

| Field | Value |
| --- | --- |
| Group | SPM `159000485013` |
| Status | Open (`2`) |
| Recipient gate | `qsiap@vixxo.com` in to / cc / support_email / description / conversations |
| Subject | Must include `New voicemail` |
| Typical type | Often `Invoice Support` or null — not SPM Vendor Relations (4046 is SF) |

**Discovery (REST):** Freshdesk search caps force type-sliced pulls. Scan:

```
group_id:159000485013 AND status:2 AND type:'Invoice Support'
group_id:159000485013 AND status:2 AND type:null
```

Then keep only tickets that pass the subject filter **and** the `qsiap@vixxo.com`
recipient gate. Full ticket load with `?include=requester,conversations` is
required before the gate (headers live on the full payload).

**Batch script:** `scripts/batch_process_qsiap.py`

## Transcript-first entity rules (mandatory)

Requester is almost always `no-reply@8x8.com`. The 8x8 body has caller ID /
duration only — **not** the spoken message.

1. Download and transcribe the **audio attachment** (`.wav` / `.mp3`) **before**
   company or contact extraction.
2. Prefer spoken company / contact / callback / SR from the Whisper transcript.
3. Treat 8x8 caller ID as a **contact hint only** when it looks like a person
   (`LAST,FIRST` → `First Last`). Never use caller ID labels as company:
   - `WIRELESS CALLER`, `Unknown`, `User ####`
   - `LAST,FIRST` person forms
   - Truncated mailbox labels
4. Failed STT → leave ticket unchanged (no note / forward / resolve).

See also historical mis-vetting notes in
`sp-inbound-vetting/reference/troubleshooting.md` (caller-ID-as-company).

## Classification and routing

Classify from the **transcript** using [categories.md](categories.md) and
[routing-actions.md](routing-actions.md).

### Already-on-QSIAP (AP categories)

When category is **Billing / Invoice Support** or **Payment Information**:

1. Post private internal note (triage template + transcript + vetting).
2. Set `type: Invoice Support` when missing.
3. Merge tags: `qsiap-source`, `voicemail-triaged` (and `sp-vetted` when posture
   is Known SP).
4. Set `cf_sp` when Known SP name/number is resolved; else `Unknown`.
5. **Do not forward** to `aphelp@vixxo.com` — the ticket is already on QSIAP.
6. **Leave Open** when callback is Yes/Recommended (AP still needs to act).
7. **Resolve** only for no-forward branches (foul language, &lt;10s, blank/minimal).

### Misroute off QSIAP

When category is **not** AP (COI, onboarding, SPM/sourcing, VixxoLink, SR, etc.):

1. Post internal note documenting misroute + transcript + vetting.
2. **Forward** to the normal triage recipient for that category.
3. Resolve after forward, with `cf_sp` when known.
4. Keep tags `qsiap-source` + `voicemail-triaged`.

### Salesforce

- **Billing / Invoice Support** and **Payment Information:** Freshdesk
  **only** — Account/Contact lookup for the packet is OK; **do not** create
  SF Cases or Tasks; **do not** forward Payment/past-due inquiries to SPM.
- All other categories: same Lead/Case/Account/Contact searches and Task /
  Case create rules as other sources
  ([salesforce-notes.md](salesforce-notes.md)). Include `Freshdesk #{id}` and
  `qsiap@vixxo.com` in Case/Task bodies for dedupe.

## Dedupe

Same audio may also land in Outlook **VM** (Vendor Relations). Triage once;
link both Freshdesk and Outlook ids in the packet. Prefer the Freshdesk QSIAP
ticket as the write target when both exist.
