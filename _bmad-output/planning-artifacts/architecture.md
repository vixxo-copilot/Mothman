# Architecture Overview

This lightweight architecture file exists to unblock BMAD review workflows that
require a canonical architecture reference.

## Current template architecture

- Repository-first bootstrap template with no runtime application services.
- Root onboarding artifacts:
  - `README.md`
  - `docs/setup.md`
  - `LICENSE`
- Root agent-context artifacts:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.cursorrules`
- Rule-pack location for future expansion:
  - `.cursor/rules/`

## Implementation constraints

- Keep template content generic and work-only.
- Use placeholder-driven identity fields (`{{employee_name}}`, `{{employee_role}}`).
- Keep secrets/local artifacts out of git via root `.gitignore`.
- Preserve portability for macOS/Linux environments.
