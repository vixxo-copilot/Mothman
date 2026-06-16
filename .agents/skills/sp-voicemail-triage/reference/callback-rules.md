# SP Voicemail — Callback Rules

Output **Callback required**: `Yes`, `Recommended`, or `No`.

Always cite transcript phrases in **Callback rationale**.

## Yes — callback required

Set **Yes** when any of these apply:

| Signal | Examples |
| --- | --- |
| Explicit callback request | "call me back", "please return my call", "need someone to call me" |
| Blocking issue | can't work, account locked, compliance hold, dispatch blocked |
| Time-sensitive deadline | "need answer today", "job tomorrow morning", "store opening" |
| Escalation / frustration | repeated attempts, "third time calling", "no one has called back" |
| Unresolved dispute | payment missing, invoice rejected with no path forward stated |
| Live coordination needed | on-site now, customer waiting, emergency/no-heat/no-water |
| Question requiring lookup | cites SR/invoice # and asks for status update |

**Urgency mapping for Yes:**

| Urgency | When |
| --- | --- |
| Critical | Emergency language, customer down, same-day job at risk, explicit "urgent" |
| High | Blocking work/payment, callback promised and overdue, same-day need |
| Normal | Standard callback request with business-day timeline |
| Low | Non-blocking question with flexible timeline |

## Recommended — callback helpful

Set **Recommended** when:

- Caller left detailed info but said "no rush" or "when you get a chance"
- Issue may be resolved by email/ticket update without a live call
- Partial information — lookup might answer without calling back
- FYI with optional follow-up ("just wanted you to know…")

State what non-call action might suffice (email, ticket note, VixxoLink check).

## No — callback not required

Set **No** when:

| Signal | Examples |
| --- | --- |
| Informational only | "calling to confirm we received…", "just an FYI" |
| Already resolved in message | "disregard, figured it out", "issue fixed" |
| Wrong number / non-SP | not related to Vixxo work |
| Duplicate / superseded | same issue reported on an open ticket with no new ask |
| Marketing / solicitation | sales pitch, unrelated vendor |
| Complete self-service path given | "I submitted through the portal as instructed" with no open ask |

When **No**, still capture transcript and category for records.

## Edge cases

**Callback number only, no ask:** If they leave a number but no clear request,
set **Recommended**, category **General Inquiry**, urgency **Normal**.

**Auto-attendant / system message:** Not an SP voicemail — note and skip triage.

**Very short / garbled audio:** Transcript what you can; set confidence **Low**;
default **Recommended** unless clear **No** signals.

**Angry tone without explicit callback ask:** Treat as **Yes** — frustration
implies failed prior contact.
