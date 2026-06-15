# Default Outlook Category Taxonomy

Customize this file to match {{employee_name}}'s work. The agent maps these
rules to **existing Outlook category names** from `list-outlook-categories`.
Rename categories here to match the mailbox, or approve creation of missing
ones.

Rules are evaluated **top to bottom**. First match wins.

## Category rules

### Action Required

**Outlook name:** `Action Required`  
**Color (if creating):** `preset0` (red)

Needs a reply, decision, or same-day handling.

**Signals:**

- Direct ask to {{employee_name}} (question, approval, review, sign-off)
- `@mention` or "action needed" / "please respond" language
- `importance:high`
- Subject contains: `action required`, `approval needed`, `please review`,
  `response requested`, `decision needed`
- Sender is manager, direct report, or active project stakeholder with an open
  ask

### Waiting

**Outlook name:** `Waiting`  
**Color (if creating):** `preset5` (yellow)

User already acted; blocked on someone else.

**Signals:**

- User was last sender in thread and no new ask to user
- Body preview: `following up`, `any update`, `pending your`, `awaiting`
  combined with evidence user already responded
- Subject starts with `Re:` or `Fwd:` and thread is outbound-follow-up shaped

### Meeting

**Outlook name:** `Meeting`  
**Color (if creating):** `preset7` (blue)

Calendar and scheduling traffic.

**Signals:**

- Subject contains: `invitation`, `accepted:`, `declined:`, `canceled:`,
  `updated invitation`, `meeting`, `calendar`
- Body preview references Teams/Zoom/Webex join link or meeting time change

### Finance

**Outlook name:** `Finance`  
**Color (if creating):** `preset3` (green)

Invoices, payments, AP/AR, and billing threads.

**Signals:**

- Subject/body: `invoice`, `payment`, `remittance`, `past due`, `statement`,
  `billing`, `AP`, `accounts payable`, `wire`, `W-9`, `1099`
- Sender domains tied to AP help desk, finance, or accounting workflows

### Vendor / Provider

**Outlook name:** `Vendor`  
**Color (if creating):** `preset4` (teal)

External service provider operations (not finance-specific).

**Signals:**

- Subject/body: `service request`, `SR#`, `SR `, `work order`, `dispatch`,
  `technician`, `quote`, `COI`, `coverage`, `provider`
- Known SP / vendor domains or Freshdesk provider-facing threads

### Projects

**Outlook name:** `Projects`  
**Color (if creating):** `preset8` (purple)

Active initiative or project delivery threads.

**Signals:**

- Subject contains project names, client program codes, or `kickoff`, `status`,
  `milestone`, `deliverable`, `SOW`
- Cross-functional delivery thread with timeline or scope language

### Reports

**Outlook name:** `Reports`  
**Color (if creating):** `preset11` (gray)

Automated or recurring operational reports.

**Signals:**

- Subject: `report`, `dashboard`, `weekly summary`, `metrics`, `export`,
  `scheduled`
- Sender is `noreply`, `no-reply`, `notifications`, or `donotreply`
- Has attachment and body preview is mostly boilerplate / snapshot language

### Internal

**Outlook name:** `Internal`  
**Color (if creating):** `preset9` (cranberry)

General internal Vixxo traffic without a sharper category above.

**Signals:**

- Sender `@vixxo.com`
- Team updates, policy notes, HR/IT broadcast without a direct ask

### FYI

**Outlook name:** `FYI`  
**Color (if creating):** `preset13` (steel)

Informational mail; no action expected.

**Signals:**

- Newsletter / digest / "for your information" / "no action needed"
- CC-only informational thread without a question to the user
- Leadership broadcast or industry news distribution lists

### Low Priority

**Outlook name:** `Low Priority`  
**Color (if creating):** `preset14` (dark-steel)

Safe to defer beyond this week.

**Signals:**

- Marketing, events, webinars, training promos, recruiting blast
- Social platform notifications
- No work relevance after applying rules above

## Customization

To override for a run, the user may say:

- "Map Finance to `AP`"
- "Skip Low Priority"
- "Only categorize last 24 hours in Inbox"
- "Append, don't replace existing categories"

Persist recurring overrides in this file when the user asks to save preferences.
