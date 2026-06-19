# Prioritization Rubric

Score each normalized work item, then bucket into P0–P3. Higher score wins
within the same bucket.

## Score factors (additive)

| Signal | Points | Notes |
| --- | ---: | --- |
| FD priority Urgent (4) | +40 | Also SF Priority `High` |
| FD priority High (3) | +25 | SF Priority `Medium` → +15 |
| SLA breach or `due_by` past | +35 | `fr_due_by` past → +20 |
| SLA due within 4 hours | +25 | |
| Email importance `high` | +20 | |
| Email flagged | +15 | |
| Tag **Ask** with no reply >24h | +20 | |
| Tag **Decision** (RSVP, approval) | +25 | |
| Meeting prep dependency ≤90 min | +30 | Related case/ticket/email |
| Open FD status (not Pending) | +10 | Pending waiting on requester → −10 |
| Stale owned Case/Task >7d no activity | +15 | |
| Cross-surface duplicate (mail + ticket) | +10 | Same issue in two queues |
| FYI-only content | −30 | |
| Pending FD waiting on customer | −15 | |
| Automated/no-ask mail | −40 | See SKILL deprioritize list |

## Buckets

| Bucket | Score range | Guidance |
| --- | --- | --- |
| **P0** | ≥70 | Do first; SLA, urgent ticket, or imminent meeting prep |
| **P1** | 45–69 | Today before EOD; actionable asks and high-priority cases |
| **P2** | 20–44 | This week; important but not time-critical |
| **P3** | <20 | Defer, delegate, or archive after skim |

Cap **P0 at 5**. If more qualify, keep highest scores and note overflow in P1.

## Calendar fit

When assigning **Focus blocks**, match item type to gap length:

| Gap | Good fit |
| --- | --- |
| ≤15 min | Single email reply, FD note skim, SF task update |
| 15–45 min | 2–3 emails, one FD ticket, short case review |
| 45–90 min | Deep FD/SF work, batch similar replies |
| ≥90 min | Queue sweep, multi-ticket thread, case research |

Never stack more work into a block than the gap duration suggests.

## Tie-breakers (in order)

1. Nearest due date / SLA
2. Highest raw priority (FD/SF)
3. Oldest untouched (created or last inbound from customer)
4. Email before internal-only tasks when customer-facing
