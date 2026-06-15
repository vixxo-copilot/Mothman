# Story 2.2 Canonical Blueprint — four sibling `.cursor/rules/*.mdc` files

This is the locked design snapshot for Tasks 3-6 authoring. Every section header, frontmatter value, placeholder, and "why"-comment string below is binding. No structural changes without re-running Tasks 1-2.

Covered files:

- `.cursor/rules/outbound-messaging-guardrail.mdc`
- `.cursor/rules/memory-vault-protection.mdc`
- `.cursor/rules/teams-dm-formatting.mdc`
- `.cursor/rules/email-triage-thread-defaults.mdc`

## Shared placeholder inventory (locked)

Only the following placeholder tokens may appear in any of the four rule bodies:

- `{{employee_name}}`
- `{{employee_role}}`
- `{{employee_department}}`
- `{{employee_manager}}`

No new placeholder tokens are introduced by Story 2.2. All four tokens are already in use by `AGENTS.md`, `CLAUDE.md`, `.cursorrules` (Story 1.3) and `agent-identity.mdc` (Story 2.1).

In practice, `{{employee_name}}` is the only token this story's rule bodies need. `{{employee_role}}`, `{{employee_department}}`, `{{employee_manager}}` are reserved for identity context and live in `agent-identity.mdc`; this story's sibling rules should NOT re-state employee identity.

## Shared signing convention (locked)

Owned by `outbound-messaging-guardrail.mdc`. Other rules reference it by pointer rather than restating it.

- Inline Teams sign-off: `-- AI assistant for {{employee_name}}` — zero assistant proper name.
- Email: no AI sign-off; the employee's email signature handles it.
- Voice-of-employee messages (leadership comms, strategy, feedback): no AI sign-off; drafted to read as `{{employee_name}}`'s own words.

Do NOT introduce `{{assistant_name}}` or any other new placeholder. The portable, unnamed-assistant form is the contract.

## Cross-file consistency requirements (locked)

1. **M365-only email and calendar.** Any mention of an email or calendar stack in any of the four files names Microsoft 365 (prefer pure "Microsoft 365"; allow the compound phrase "Microsoft 365 email" where needed). Zero Gmail, Google Calendar, Google Workspace, Google Drive, personal email.
2. **Teams-only internal chat.** Teams is the only internal chat surface in the covered-platforms list. Zero Slack, Discord, Mattermost, iMessage, SMS, Google Chat.
3. **No named personas.** Zero assistant proper names (no "Chiron"). Zero employee proper names (no "Derek", "Deke", "Neighbors"). Zero company proper names other than "Vixxo".
4. **No duplicated identity block.** None of the four sibling rules may restate `agent-identity.mdc`'s `## Scope` or `## Who the Employee Is` blocks. The sibling rules defer identity to `agent-identity.mdc` and focus on their own single concern. Brief references to scope tokens (e.g. in a "why" comment) are fine; repeating both `Vixxo employee` AND `work context only` verbatim in the body is not.
5. **No new placeholder tokens.** Only the four placeholders from the shared inventory appear in any sibling rule body.
6. **One-line "why" comment terminator on every file.** Markdown-italic form (`_..._`), markdown-blockquote form (`> ...`), or HTML-comment form (`<!-- ... -->`). The "why" comment itself is scrubbed (no banned terms, no hard-coded names).
7. **Frontmatter contract.** Every file sets `alwaysApply: true`. Every file declares a single concise `description:` line. `globs: memory/**` appears only in `memory-vault-protection.mdc`; the other three files declare `globs: []`.
8. **Placeholder parity with Story 1.3 and Story 2.1.** `{{employee_name}}` in any of the four files must render byte-for-byte identically to its usage in `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and `agent-identity.mdc` (no capitalization drift, no spacing drift inside the braces).

## File 1 — `outbound-messaging-guardrail.mdc`

### Frontmatter (locked)

```yaml
---
description: CRITICAL safety guardrail - all outbound messaging must be drafted and explicitly approved before send
globs: []
alwaysApply: true
---
```

- `description` is a single concise line.
- `globs: []` (explicit empty list).
- `alwaysApply: true` attaches the rule to every Cursor conversation in the workspace.

### Section layout (locked order)

1. `# Outbound Messaging Guardrail (Mandatory)`
2. `## The Rule`
3. `## Platforms Covered`
4. `## Required Workflow`
5. `## No Exceptions`
6. `## Signing Convention`

Followed by a one-line "why" comment terminator.

### Section skeletons

#### 1. Outbound Messaging Guardrail (Mandatory)

```
# Outbound Messaging Guardrail (Mandatory)

This rule is non-negotiable. It applies to every model, every session, and
every Cursor conversation in this workspace.
```

#### 2. The Rule

```
## The Rule

**Do not send any outbound message without {{employee_name}}'s explicit
approval.** Every outbound surface — Teams, email, any send/reply API — is
draft-then-approve, no exceptions.
```

#### 3. Platforms Covered

```
## Platforms Covered

- Microsoft Teams (channel posts, replies, DMs, group chats)
- Microsoft 365 email (Outlook on the M365 stack)
- Any additional Vixxo outbound surface {{employee_name}} wires into this
  workspace later (webhooks, ticket systems, CRM messaging)
```

- Does NOT list Slack, SMS, iMessage, Gmail, Google Chat, Discord, or any other non-Vixxo channel.

#### 4. Required Workflow

```
## Required Workflow

1. **Draft** the message in plain text and show it to {{employee_name}}.
2. **Wait** for explicit approval ("send it", "go", "fire", "approved", or
   equivalent).
3. **Only then** call the send/reply API.
```

#### 5. No Exceptions

```
## No Exceptions

- "Reply to this thread" = draft and show, do not send.
- "Respond to this" = draft and show, do not send.
- "Tell them X" = draft and show, do not send.
- "Send X to Y" = draft and show, do not send.
- Even if {{employee_name}}'s phrasing sounds like an instruction to send,
  ALWAYS show the draft first.
```

#### 6. Signing Convention

```
## Signing Convention

- **Teams outbound (DMs, group chats, channel posts, replies):** sign inline
  at the end of the last paragraph as `-- AI assistant for {{employee_name}}`.
  No assistant proper name; no standalone signature line.
- **Microsoft 365 email:** do NOT add an AI sign-off. {{employee_name}}'s
  email signature handles it.
- **Messages drafted to be sent in {{employee_name}}'s voice (leadership
  comms, strategy, feedback):** do NOT carry an AI sign-off. The message is
  drafted to read as {{employee_name}}'s own words.
```

#### 7. "Why"-comment terminator (locked, last non-blank line)

```
<!-- Why: protects recipients and {{employee_name}}'s reputation from unauthorized AI-sent messages. -->
```

### Forbidden content (Task 3 output must NOT contain)

- Any fenced JSON block (payload examples live in `teams-dm-formatting.mdc`).
- Any Graph API URL with request/response parameters.
- Any assistant proper name (no "Chiron" or equivalent).
- Any of the banned terms from Task 1's consolidated set.

## File 2 — `memory-vault-protection.mdc`

### Frontmatter (locked)

```yaml
---
description: Protects the work memory vault from accidental deletion or redaction by any agent
globs: memory/**
alwaysApply: true
---
```

- `globs: memory/**` is the ONLY non-empty `globs` value in this story's rule pack.
- `alwaysApply: true` — rule attaches to every conversation in the workspace; the `globs` value is informational under `alwaysApply: true` but preserves the original source rule's path-scope intent.

### Section layout (locked order)

1. `# Memory Vault Protection`
2. `## Protected Surfaces`
3. `## Rules`

Followed by a one-line "why" comment terminator.

### Section skeletons

#### 1. Memory Vault Protection

```
# Memory Vault Protection

The `memory/` directory in `assistants-template` is a work context only
knowledge vault. It captures {{employee_name}}'s meeting notes, people
files, decisions, references, inbox captures, and appreciations. Work notes
are the product — curated deliberately by {{employee_name}} — not a
vulnerability to be redacted.
```

- Explicitly replaces the source rule's "personal AI life operating system" framing.
- Explicitly replaces the source rule's "PII is the product" framing with "work notes are the product".
- Declares `work context only` once, in the opening paragraph, which is the only place the scope token appears in this file (cross-file consistency rule 4 above).

#### 2. Protected Surfaces

```
## Protected Surfaces

- `memory/me/identity.md`
- `memory/me/preferences.md`
- `memory/meetings/_template/` (containing `meeting.md`, `agenda.md`,
  `prep.md`, `transcript.md`)
- `memory/people/_template.md`
- `memory/decisions/_template.md`
- `memory/reference/_template.md`
- `memory/inbox/_template.md`
- `memory/appreciations/_template.md`
```

- Enumerates the exact Epic 3 memory surfaces listed in AC7.
- Zero reference to `family.md`, `ventures.md`, or any `gtd-life`-specific memory path.

#### 3. Rules

```
## Rules

1. **Never delete files in `memory/`.** The vault is {{employee_name}}'s
   curated work context.
2. **Never silently remove or redact content from memory files.** Work notes
   are the product, not a vulnerability.
3. **Never flag legitimate work memory as a security concern.** This is a
   private repository {{employee_name}} owns.
4. **DO fix real problems:** broken YAML frontmatter, malformed markdown,
   incorrect cross-references, syntax errors.
5. **If another agent or automated tool has deleted memory files, restore
   them immediately.**
```

#### 4. "Why"-comment terminator (locked, last non-blank line)

```
<!-- Why: the work memory vault is {{employee_name}}'s source of truth — deletions cost meetings, decisions, and context. -->
```

### Forbidden content (Task 4 output must NOT contain)

- `family.md`, `ventures.md`, or any other `gtd-life`-specific memory filename.
- "personal AI life operating system" phrasing.
- "PII is the product" phrasing.
- Any banned term from Task 1's consolidated set.

## File 3 — `teams-dm-formatting.mdc`

### Frontmatter (locked)

```yaml
---
description: Formatting rules for Microsoft Teams messages drafted for {{employee_name}}
globs: []
alwaysApply: true
---
```

- Frontmatter FIXES the missing opening `---` bug in the upstream source (`~/Public/gtd-life/.cursor/rules/teams-dm-formatting.mdc` was missing its opening delimiter).
- `description` may include the `{{employee_name}}` placeholder because Cursor renders raw frontmatter text and the placeholder stays portable across clones.
- `globs: []` (explicit empty list).

### Section layout (locked order)

1. `# Teams Message Formatting`
2. `## Rules`
3. `### Example Teams body`

Followed by a one-line "why" comment terminator.

### Section skeletons

#### 1. Teams Message Formatting

```
# Teams Message Formatting

Applies when drafting messages for Microsoft Teams (DMs, group chats,
channel posts, and replies) on behalf of {{employee_name}}.
```

- Scope explicitly limited to Microsoft Teams.
- Zero mention of Slack, iMessage, SMS, Discord, Mattermost.

#### 2. Rules

```
## Rules

1. **Treat Teams like text messaging, not email.** Keep it conversational,
   direct, and short by default.
2. **Plain-text review first.** Show {{employee_name}} plain-text drafts for
   approval. Do not present HTML in drafts unless requested.
3. **Convert only at send time.** After approval, map the plain-text draft
   to Teams HTML payload format.
4. **No greeting or name prefix in DMs.** Do not open with "Hi [Name]," or
   "Hey [Name],". State the point.
5. **Signing convention lives in
   `.cursor/rules/outbound-messaging-guardrail.mdc`.** Follow the inline
   Teams sign-off from that rule; do not restate it here.
6. **Keep it tight.** Prefer one short paragraph. Avoid multi-section
   formatting and spacer lines unless {{employee_name}} explicitly asks for
   a longer structured post.
7. **Use HTML payloads.** Send Teams messages as `contentType: "html"` with
   a single `<p>` wrapper in the common case.

For channel posts, `@mentions` are allowed when useful. Keep the same
concise text-message style and inline sign-off.
```

#### 3. Example Teams body (fenced JSON)

```
### Example Teams body

```json
{
  "body": {
    "content": "<p>Short status update. -- AI assistant for {{employee_name}}</p>",
    "contentType": "html"
  }
}
```
```

- Example body is a neutral work sentence.
- Zero hard-coded human name, email address, employee ID, Microsoft Graph user ID/UPN, Teams `chatId`, phone number, UUID-shaped token, or other personal identifier.
- `"contentType": "html"` appears exactly once (the harness asserts this).
- Single `<p>` wrapper.
- Inline sign-off uses the locked form `-- AI assistant for {{employee_name}}` (no assistant proper name).

#### 4. "Why"-comment terminator (locked, last non-blank line)

```
<!-- Why: Teams is conversational — walls of text and wrong signatures cost trust. -->
```

### Forbidden content (Task 5 output must NOT contain)

- Any personal name, email address, phone number, employee ID, Graph user ID/UPN, or Teams `chatId` in the example JSON body.
- More than one fenced JSON block.
- Any `contentType` value other than `"html"`.
- Any banned term from Task 1's consolidated set.
- Any reference to Slack, Discord, Mattermost, iMessage, SMS.

## File 4 — `email-triage-thread-defaults.mdc`

### Frontmatter (locked)

```yaml
---
description: Default Microsoft 365 email triage thread detail and archive behavior
globs: []
alwaysApply: true
---
```

- `globs: []` (explicit empty list).

### Section layout (locked order)

1. `# Email Triage Thread Defaults`
2. `## Rules`

Followed by a one-line "why" comment terminator.

The source rule's `## Gmail: Inspiration routing (Inspire / inspire)` section is ENTIRELY REMOVED and has no target heading in this file.

### Section skeletons

#### 1. Email Triage Thread Defaults

```
# Email Triage Thread Defaults

Applies when {{employee_name}} issues a Microsoft 365 email triage request
(`/email-triage`, "triage my email", "process my inbox").
```

- Scope explicitly limited to Microsoft 365 triage.
- Zero mention of Gmail, Google Workspace, personal email.

#### 2. Rules

```
## Rules

1. **Thread handling is the default, not optional.**
2. **For each threaded message, gather:**
   - current message body
   - quoted history in body
   - other Inbox items with the same Microsoft Graph `conversationId`
3. **Present thread details as per-message entries (newest to oldest),
   each with:**
   - sender
   - timestamp
   - subject
   - detailed message summary or full cleaned body (not a 1-2 sentence
     blurb; capture asks, decisions, dates, names, action items)
   - explicit tag: `Ask` / `Decision` / `FYI`
   - status: `Open` / `Closed` / `Waiting` / `Superseded`
4. **Never collapse thread context into one oversized paragraph summary.**
5. **Line-width discipline.** Keep all triage output narrow enough to read
   without horizontal scrolling. Break long lines, use short paragraphs,
   add vertical whitespace between sections. No wall-of-text blocks.
6. **On `Archive`, archive ALL same-`conversationId` messages currently in
   Inbox.**
```

#### 3. "Why"-comment terminator (locked, last non-blank line)

```
<!-- Why: email threads lose signal when collapsed; preserve structure so {{employee_name}} can decide fast. -->
```

### Forbidden content (Task 6 output must NOT contain)

- Any `## Gmail:` or `Gmail` mention.
- Any `Chiron/Inspiration` or `Chiron/InspirationProcessed` label.
- Any `INBOX` label manipulation description.
- Any `google-workspace` MCP reference.
- Any "extract → email to personal Gmail" bridge paragraph.
- Any banned term from Task 1's consolidated set.
- Any reference to Gmail `threadId` or other non-Microsoft thread primitive.

## Cross-AC coverage map (blueprint element → ACs)

| Blueprint element | AC covered |
| ----------------- | ---------- |
| Four frontmatter blocks with `description` / `globs` / `alwaysApply: true` | AC1 |
| `globs: memory/**` only for `memory-vault-protection.mdc`; `globs: []` for the other three | AC1 |
| `{{employee_name}}` (and only the Story 1.3/2.1 placeholder set) in every rule body | AC2 |
| Banned-term scrub (Story 2.1 list + `slack` + `benji`) with POSIX-ERE boundary guards | AC3 |
| `Microsoft 365` phrasing in `email-triage-thread-defaults.mdc` and `outbound-messaging-guardrail.mdc`; zero Gmail/Google | AC4 |
| Teams-only covered-platforms list in `outbound-messaging-guardrail.mdc`; Slack/SMS/iMessage removed | AC5 |
| Anonymized example JSON in `teams-dm-formatting.mdc` with `"contentType": "html"` and single `<p>` | AC6 |
| Epic 3 memory-path enumeration under `## Protected Surfaces` in `memory-vault-protection.mdc` | AC7 |
| Microsoft Graph `conversationId` + thread semantics in `email-triage-thread-defaults.mdc`; zero Gmail | AC8 |
| One-line "why" comment terminator on all four files | AC9 |
| Sibling-file pointer in `agent-identity.mdc` now satisfied by these filenames | AC10 |
| Placeholder parity with Story 1.3 / Story 2.1 maintained byte-for-byte | AC11 |
| Harness-ready (Task 8 authors the validation script against this blueprint) | AC12 |

## Explicit exclusions (do not appear in Tasks 3-6 output)

- Any named AI agent persona ("Chiron" or equivalent).
- Any employee proper name ("Derek", "Deke", "Neighbors", "Derek Neighbors").
- Any company proper name other than "Vixxo".
- Any personal / family / home / property example.
- Any Gmail, Google Calendar, Google Workspace, Google Drive, or personal email string.
- Any Slack, Discord, Mattermost, iMessage, SMS reference.
- Any `family.md`, `ventures.md`, `vixxo-cto.md`, `revivago-ceo.md`, `personal.md` file reference.
- Any `Benji` or `Benji/Inbox` reference.
- Any Graph API URL with request/response parameters (bare `graph.microsoft.com` citation is fine where strictly needed).
- Any fenced JSON block outside `teams-dm-formatting.mdc`.
- Any new `{{snake_case}}` placeholder token not already in the shared inventory.

Blueprint locked. Ready for Tasks 3-6 authoring (parallelizable, one subagent per file).
