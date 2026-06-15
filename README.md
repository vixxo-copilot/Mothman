# assistants-template

`assistants-template` is the Vixxo work assistant starter repository for employees who need a clean, work-only AI assistant baseline.

## Quickstart

### Prerequisites

- `git`
- `node` (Active LTS recommended)
- `npx`

### Bootstrap in under 15 minutes

1. Clone the repository:

   ```bash
   git clone <repo-url> assistants-template
   cd assistants-template
   ```

2. Install the shared skill bundle:

   ```bash
   npx skills add vixxo-copilot/agent-skills
   ```

3. Continue setup with the full onboarding guide: [`docs/setup.md`](docs/setup.md)

## Help

- Check project documentation in `docs/` for setup and MCP guidance.
- If onboarding is blocked, open an internal tracker ticket and post the ticket link in the Vixxo AI support channel so the platform team can triage quickly.
- PII guardrail: `.github/pii-denylist.txt` (deny-list) + `docs/pii-denylist.md` (policy doc) + `.github/workflows/pii-denylist.yml` (CI checks).
