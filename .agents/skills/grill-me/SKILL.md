---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

# Grill Me

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## When to finish

When major branches of the design tree are resolved, summarize:

1. Decisions made (with rationale)
2. Open questions or explicit deferrals
3. Recommended next step (for example PRD, issues, or implementation)

## Guardrails

- Do not start implementing until the user confirms the shared understanding is sufficient.
- Do not batch many questions in one message; one question at a time keeps the interview focused.
- Prefer codebase exploration over asking the user for facts already present in the repo.
