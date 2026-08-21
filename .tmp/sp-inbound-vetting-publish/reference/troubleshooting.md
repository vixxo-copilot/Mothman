# SP Inbound Vetting — Troubleshooting

Findings from batch review (2026-06-24 re-vet, 180 tickets).

## Symptom: 0 Known SP across entire batch

**Root cause:** Batch shell scripts could not reach Gateway — usually because
Gateway was queried via direct HTTP without auth, while **Cursor Gateway MCP**
(OAuth, no file token) was not used.

**Fix (interactive Cursor run — preferred):**

1. Confirm **gateway** MCP is enabled and green in Cursor Settings → MCP.
2. Run vetting from this agent session; Gateway tools resolve through
   `project-0-assistant-CGagner-gateway` (same as June 16 dry-run).
3. Use `gateway_search_invoices(serviceProviderNumber=KS#####)` when KS is
   present; `searchString` alone may return empty.

**Fix (batch shell scripts):**

1. Interactive vetting: enrich dry-run JSON with Gateway MCP results, then
   `python scripts/live_run_batch.py --data .tmp/gateway-mcp-revet-*.json`.
2. Shell `mcp_http.py` does not use Cursor OAuth — expect empty Gateway in
   unattended scripts unless optional bearer tokens are configured locally.
3. Re-run batch; summary includes `gateway_health` probe (informational only
   when using `--data` enrichment).

**Example — Allied Locksmiths (#56995, #56502):**

- Company search alone returned empty; **SF Account** (`Type = Service Provider`)
  had `Service_Provider_Number__c = KS68937`.
- Gateway: `gateway_search_invoices(serviceProviderNumber=KS68937)` →
  `Allied Locksmiths Of Youngstown`.
- Posture: **Known SP**; do not leave as `unknown-sp`.
- Do **not** use bare city token `Youngstown` as a last-name fallback (noise).
  Full company string `ALLIED LOCKSMITHS OF YOUNGSTOWN` is valid to search.

---

## Symptom: `cf_sp` contains email body text

**Examples:** FD #58450, #58179 — paragraph-length `cf_sp` values.

**Root causes:**

1. Invalid `cf_sp` on ticket was reused as company hint.
2. No max-length / sentence validation on extracted company strings.

**Fixes (in skill):**

- `is_valid_company_string()` — max 80 chars, reject `?`, SR numbers, boilerplate.
- Do not read garbage `cf_sp_current` as company source.
- Overwrite invalid existing `cf_sp` when a valid company is extracted.

---

## Symptom: Client site name used as SP company

**Example:** FD #58461 — subject `Certificate - Vixxo Kansas, LLC` is the
**client location**, not the service provider.

**Fix:** Reject subject lines matching `Certificate/COI - Vixxo …`; prefer
signature/body SP name and requester email domain (`inszoneins.com`).

---

## Symptom: Contact person name used as company

**Examples:** `Erin Goettsche`, `Brandin Kaeser`, `Certs` as company.

**Fix:** Only fall back to requester display name when it is not a person name
(two capitalized tokens without LLC/Inc) and not a generic mailbox label.
Prefer signature company + email domain Gateway search.

---

## Symptom: KS / SP # in email not driving Gateway lookup

**Examples:** FD #54635 `Alpha Concepts LLC - KS101031`; FD #58330 `#90988`.

**Fix:** Parse `KS#####` and `#90988` patterns from subject, body, and company
string; pass as `ks_number` to `gateway_search_invoices(serviceProviderNumber=…)`
and `gateway_swm_get_provider`.

---

## Symptom: Company extracted but still `unknown-sp`

**Expected when:** Gateway unreachable in batch shell, or SP not yet in Siebel.

**Do not** run broad city-only Gateway searches (e.g. `Youngstown` from
Allied Locksmiths address) — they return huge noisy result sets. Use full
company name, KS number (`serviceProviderNumber`), or corporate email domain.

**Skill behavior:** Set `cf_sp` to extracted company (e.g. `PEAK SEASON LLC`)
with `unknown-sp` tag until Gateway returns SP #.

**Example:** FD #58785 — COI from Peak Season; Gateway lookup required after
token fix.

---

## Symptom: SF queue SOQL returns 0 Cases

**Root cause:** Queue Id not discovered, wrong `DeveloperName`, or Cases owned
by user instead of queue.

**Fix:**

1. Run queue discovery SOQL in [queues.md](queues.md).
2. Confirm Case `OwnerId` matches queue Id — not a person user.
3. Check org-specific routing (RecordType, custom assignment fields).

---

## Symptom: Payment ask vetted in SF queue but not routed to AP Help

**Expected:** Skill recommends AP Help forward in the Case Task — it does **not**
auto-forward.

**Fix:** Review Case Task for **Recommended routing** block. Operator must
approve before any forward to `aphelp@vixxo.com`.

---

## Symptom: COI Case forwarded to AP Help incorrectly

**Root cause:** Payment keywords in boilerplate triggered AP routing on a COI-primary ask.

**Fix:** Re-read dominant ask from subject/body. COI/compliance signals → **Stay in SF**.
Use routing table in [queues.md](queues.md). Hand certificate review to
`vixxo-coi-review` after identity vet.

---

## Recommended run checklist

1. Confirm `gateway_health.ok` in batch summary (AP Help scripts) or Gateway MCP green (SF runs).
2. Spot-check 3 items: one COI Case (stay SF), one ksonboarding payment ask (AP draft), one aphelp ticket.
3. Review items where posture is Unknown with no company, or AP forward recommended without SP #.
4. Confirm SF queue Ids populated in [queues.md](queues.md) after discovery SOQL.

---

## Symptom: Freshdesk MCP `search_tickets` returns HTTP 400

**Root cause:** Freshdesk `/api/v2/search/tickets` requires the `query` param
value to be wrapped in double quotes (e.g. `"status:2"`). The upstream
`freshdesk-mcp` npm package passed unquoted filters.

**Fix (2026-06-25):** Workspace launcher
(`.cursor/bin/run-freshdesk-mcp.py`) vendors `freshdesk-mcp@1.1.1` with a
patch that auto-quotes the filter. Pass the expression only — e.g.
`status:2`, `created_at:>'2026-06-24'`, or
`group_id:159000485013 AND status:2`. Optional `page` is supported.
Restart the Freshdesk MCP server in Cursor after pulling the fix.

**Workaround (pre-fix):** Use REST with quoted query via skill batch scripts
(`search_all()` in `dry_run_batch.py`) or list API
`/api/v2/tickets?updated_since=…` plus client-side filters.

---

## Future enhancements (not yet implemented)

| Gap | Proposal |
| --- | --- |
| SF queue batch script | `dry_run_batch.py --queue coi` pulling Cases via SOQL |
| SF Contact → Account | When Lead missing, resolve Contact email → Account name → Gateway |
| ServiceTitan senders | Map `noreply@onservicetitan.com` to company in HTML body / subject |
| Alternate body emails | Always Gateway-search signature emails not in requester field |
| Confidence tag | Add `sp-vet-low-confidence` when company from contact name only |
