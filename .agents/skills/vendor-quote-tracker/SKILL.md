---
name: vendor-quote-tracker
description: >-
  Tracks Sign and Lighting vendor quote outreach for Storage Star / Easter Egg
  ESS sites by cross-referencing sent mail, inbox replies, and optional banner
  workbooks. Use when the user asks to check vendor emails, quote status, who
  responded, chase vendors, or Storage Star installer outreach progress.
---

# Vendor Quote Tracker

Work-only skill for AJ Sheth's Storage Star / Easter Egg facility quote
program (~60 ESS sites). Phase 1: debrand + temporary banners (target July).
Phase 2: permanent signage (separate quotes later).

## When to use

- "Check vendor emails" / "quote status" / "who replied"
- Storage Star or Easter Egg installer outreach
- Summary for Stacie on sites quoted vs outstanding

## Output format

Return in this order:

1. **Summary counts** — sent, quoted, declined, engaged (no $), no response
2. **Status table** — one row per vendor thread (ESS, site, vendor, status, detail)
3. **Blockers** — wrong vendor type, site-number confusion, dead ends
4. **Next actions** — chase list, forward-to-Stacie items, resend fixes

Status values: `Quoted` | `Declined` | `Engaged` | `No response` | `Closed`

## Workflow

### 1. Microsoft 365 auth

Call `verify-login`. If needed, run `login` and wait for user confirmation.

### 2. Pull sent vendor outreach

`list-mail-folder-messages` on `sentitems`:

- `orderby`: `sentDateTime desc`
- `top`: 50 (paginate if needed)
- `select`: `subject,toRecipients,sentDateTime,bodyPreview`

Filter to external sign/install vendors (non-`@vixxo.com` recipients). Match
subjects like `ESS`, `7xxx` site numbers, city/state, or "Quoter Request".

Extract per row: **ESS #**, **city**, **vendor email**, **sent date**.

### 3. Pull inbox vendor replies

Run separate searches (KQL values double-quoted; never combine `$search` +
`$filter` on one request):

- Known vendor domains: `olysigns`, `allysigns`, `signsafari`, `candssigns`,
  `jnlsanchez`, `signpros`
- Subject: `"Storage Star OR Extra Space OR quote"`

`select`: `subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments`

For threads with pricing or declines, call `get-mail-message` for full body.

### 4. Match sent ↔ replies

Join on subject ESS/site and vendor address. Flag:

- **Quoted** — dollar amount or formal scope/assumptions in reply
- **Declined** — e.g. manufacturer-only, no install
- **Engaged** — replied but no price yet
- **No response** — sent >48h with no external reply (note age only)

### 5. Optional workbook cross-check

If user provides or references `Storage Star Banner Count.xlsx` or Easter Egg
facility files, validate ESS numbers and banner columns (BANNER, FREESTANDING)
against email scope. Flag site-number mix-ups (e.g. 7661 vs 7662).

### 6. Internal context (non-vendor)

Include Mike Nguyen / SignPros threads (e.g. Glassboro) only when labeled
**related, not part of AJ's 60-site batch**.

Stacie expectation: **all 60 sites** quoted; report **remaining count**.

## Status table template

| ESS | Site | Vendor | Sent | Status | Detail |
|-----|------|--------|------|--------|--------|
| 7650 | Arlington Heights, IL | Guy / Oly Signs | date | Quoted | $ amount + assumptions |
| 7661 | Rockledge, FL | Jeff / Ally Signs | date | Declined | Manufacturer only |
| 7696 | Beaver Creek, CO | Sign Safari | date | Engaged | Timeline only, no $ |

## Response handling rules

| Reply type | Action |
|------------|--------|
| Quote received | Recommend forward to Stacie Hicks with ESS + $ + assumptions |
| Declined install | Flag alternate installer needed; note ESS |
| Engaged, no quote | Draft chase email (user approves before send) |
| No response | Add to chase list; suggest 48h+ follow-up |
| Site number error | Note correction before resend |

## Email draft guardrails

- Draft only — never send without explicit user approval
- No AI sign-off on email drafts (user's Outlook signature)
- Attach ART reference when resending outreach
- Use outbound messaging guardrail: show plain-text draft first

## Chase email template

Use when vendor replied but no formal price:

```
Following up on ESS [####] / [City, ST] — could you send a written quote for
Phase 1 (debrand + temporary banners)? Target install window is July [flexible].
Happy to clarify banner sizes from our takeoff if helpful.
```

## Known patterns (Storage Star)

- Outreach opener: 2021 Extra Space work → possible Storage Star conversion
- Scope bullets: remove ESS signage, caulk/cap; building banners; freestanding banners
- Permits often billed at cost + procurement fee (capture in quote summary)
- Two-phase project per Mike Nguyen: Phase 1 banners, Phase 2 permanent signs

## Trigger phrases

vendor emails, quote status, who responded, chase vendor, Storage Star quotes,
Easter Egg outreach, installer replies, forward quote to Stacie
