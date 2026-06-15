---
type: identity
scope: work
name: "{{employee_name}}"
role: "{{employee_role}}"
department: "{{employee_department}}"
manager: "{{employee_manager}}"
email: "{{employee_email}}"
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [identity, work]
---

# Identity

## Name

{{employee_name}}

## Role

{{employee_role}}

## Department

{{employee_department}}

## Manager

{{employee_manager}}

## Email

{{employee_email}}

## Work Scope

Vixxo work context only. This file records the operator's role and
reporting line for the assistants template; non-work context stays
out of scope. See `.cursor/rules/agent-identity.mdc` for the
authoritative scope declaration.

## Key References

- `.cursor/rules/agent-identity.mdc`
- `agents/personas/work.md`
- `memory/me/preferences.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.cursorrules`

<!-- Why: identity skeleton; Epic 5 setup wizard rewrites placeholders with employee answers. -->
