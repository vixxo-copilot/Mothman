---
name: sr-post-completion-review
description: >-
  Audits Vixxo Service Requests after closure, job-complete marking, invoice workflow,
  or inspection review to determine whether work was truly completed, whether notes
  prove root-cause resolution, and whether follow-on work needs an owner. Use when the
  user asks for post-SR review, closed SR audit, completion review, inspection follow-up,
  Luxottica follow-on work, or SRs closed with no action.
---

# Vixxo SR Post-Completion Review

## Purpose

Use this skill after an SR is closed, marked `Job Complete = Y`, sitting in invoice workflow, or attached to post-SR inspection notes. The output is a **completion intelligence packet**: what likely happened in the field, whether completion is proven, what follow-up is required, whether the invoice can proceed, who owns the next step, and what account intelligence should be retained.

This skill does not replace `.cursor/skills/sr-triage-pre-dispatch/SKILL.md`. It depends on that skill's Mode B decoders before it audits completion.

## When to Use

Run this skill for:

- Closed or apparently complete SRs that need quality review.
- SRs in invoice workflow where completion evidence is weak.
- Inspection work that may create follow-on actions.
- Cohort reviews by account, trade, SP, site, or time window.
- Luxottica or other high-touch account reviews where closure notes must be checked against customer workflow requirements.

Do not use this for pre-dispatch routing. Use SR triage Mode A. Do not use it for open-queue next-action bucketing. Use SR triage Mode C.

## Required Read Sequence

1. If the work is Vixxo-related, read `VIXXO.md`.
2. If an account is named, read `MAGIC/memory/accounts/_index.md`, then the account file. For Luxottica, read `MAGIC/memory/accounts/luxottica-north-america.md`.
3. Read `.cursor/skills/sr-triage-pre-dispatch/SKILL.md` and run Mode B on each SR before completion scoring.
4. Read `review-packet.md` for the packet schema.
5. Read `follow-on-action-rules.md` for deterministic follow-on, inspection, closure-note, and invoice-risk rules.
6. Read `account-example-luxottica.md` when Luxottica is the example or review account.

## Workflow

1. Confirm the review scope: single SR, cohort, account/trade window, or inspection-review batch.
2. Decode the SR with SR triage Mode B: sub-status, SR graph, asset-data lineage, recurring-failure flag, post-implementation flag, documentation quality, and quality signals.
3. Extract literal completion evidence from notes, resolution text, visit notes, inspection notes, photos, quotes, time events, and invoice-side records available to the review.
4. If quoted work is visible, referenced, approved, pending, or quote visibility is blocked in VixxoLink, run the quoted-work reconciliation path in `follow-on-action-rules.md`. Use Gateway quote data when VixxoLink quote data is unavailable or incomplete.
5. Apply `follow-on-action-rules.md`.
6. Emit the completion intelligence packet from `review-packet.md`.
7. For cohorts, aggregate repeated patterns by separate dimensions: work outcome, proof status, final operating call, follow-up required, invoice disposition, and durable account/system signal.
8. Recommend memory or action capture only when the review creates durable context or a trackable follow-up. Do not mutate memory unless the user asks for it.

## Non-Negotiable Constraints

- Never declare "no follow-up" before running the SR graph resolver and checking parent, child, sibling, and same-FWKD work.
- Never accept `Job Complete = Y` as proof of completion without a resolution note or equivalent evidence that names the diagnostic, action, and verification.
- Never use `verified-complete` unless the work product has been evaluated through photos, notes, inspection results, invoice/work-ticket evidence, customer confirmation, or customer/site sign-off in VIXLA/VixxoLink. Status flags and "job complete" language are not enough.
- Never use `verified-complete` for temporary relief when root cause, durable repair, quoted work, customer decision, compliance work, or other follow-on remains. Use `verified-temporary-relief`.
- Never treat "looks complete" as close-ready when required documentation, signed work ticket, structured resolution, photo evidence, customer/site signoff, quote support, or account workflow proof is missing. Use `not-verified-documentation-gap`, set `follow-up-required`, and name the documentation or verification correction.
- Never use a documentation gap to imply field failure. Separate work outcome from proof status and invoice disposition.
- Never mark an SR `close-ready` while medium- or high-confidence `repair-review`, follow-up, documentation, or invoice-risk signals remain unresolved.
- Never mark quoted work clean until the initial symptom, approved quote scope, and completion evidence have been reconciled.
- Never stop at a VixxoLink quote-tool failure when quoted work is visible or likely; check Gateway quote records or state Gateway was unavailable and lower confidence.
- Never treat inspection findings as informational only when they identify repair, quote, warranty, chargeback, PM, safety, compliance, or customer-decision work.
- Never create a Luxottica operating call from the customer name alone. Use Luxottica context only to calibrate workflow sensitivity and follow-up discipline.
- Never call a missing asset id a data-quality failure by itself on fixture-level work; state which recurrence, warranty, or post-implementation checks remain unresolved.
- Preserve provenance: quote the SP or inspection note before inferring diagnosis or follow-on scope.

## Output

For each SR, produce a completion intelligence packet. For cohorts, start with a run summary and then list only high-signal SR packets unless the user asks for every SR.

Use direct Vixxo operating language: work outcome, completion proof, follow-up required, invoice disposition, owner, check-back, confidence.
