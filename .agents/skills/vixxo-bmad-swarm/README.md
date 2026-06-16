# BMAD Swarm

Autonomous BMAD development pipeline: takes a story from backlog to a merged PR with zero user
interaction, using parallel subagents for story creation, implementation, and code review.
Supports single-story, next-in-backlog, and full-epic modes.

This is a **repo-portable, profile-driven** skill modeled on `linear-issue-creator`: a shared
core plus a small repo-local profile. The first time you run the swarm in a repo with no
profile, a **detection-first onboarding** auto-detects most settings and asks only the
ambiguous ones, then writes `.agents/skills/vixxo-bmad-swarm/local/profile.yaml`.

## Prerequisites

- **BMAD Method** installed in the repo (`_bmad/` present). The swarm orchestrates the BMAD
  `bmad-create-story`, `bmad-dev-story`, and `bmad-code-review` skills.
- A BMAD sprint-status file at `{implementation_artifacts}/sprint-status.yaml`.
- Optional: `linear-issue-creator` installed (the swarm reuses its profile for Linear identity).
- Optional: `gh` for PR creation; a Linear MCP for status sync.
- Optional: Cursor Bugbot / Security Review subagents for the pre-push review gate.

## Install

```bash
npx skills add vixxo-copilot/agent-skills/skills/vixxo-bmad-swarm
```

## Configure (first run)

You do not hand-write config. On first invocation in an unconfigured repo, onboarding
(`reference/onboarding.md`) detects BMAD config, base branch, `gh`, changelog setup, repo
rules, and the `linear-issue-creator` profile, then asks only:

- Linear integration on/off (pure-BMAD repos choose off),
- epic PR strategy (single PR at end vs PR per story),
- confirm/override branch + commit conventions.

It writes `.agents/skills/vixxo-bmad-swarm/local/profile.yaml` (gitignored). If you prefer to write
it by hand, copy a shipped example:

- `config/example.profile.yaml` — generic template.
- `config/bridge.profile.yaml` — Bridge conventions (Linear-backed, changelog, kickoff rule).

## What the profile controls

The swarm profile holds **only swarm-specific** settings; Linear identity (team/owner/assignee)
is read from the `linear-issue-creator` profile so the two never drift.

- `linear_integration` — `enabled` | `disabled` (off = pure-BMAD pipeline)
- `branch` / `commit` — branch templates and commit message format
- `changelog` — whether to emit changelog fragments, and the rule that defines their shape
- `pr` — base branch, tool, and epic PR strategy
- `review` — BMAD adversarial review toggle, pre-push Bugbot toggle, security-review trigger globs
- `linear_tooling` — Linear MCP + optional fallback CLI
- `rule_refs` — optional repo rules (kickoff, lifecycle); used if present, skipped if absent

See `config/profile-schema.yaml` for the full schema and `reference/onboarding.md` for the
first-run flow.

## Usage

```
swarm 0-1          # single story by key
swarm next         # next backlog story
swarm epic-3       # full epic, looping story by story
```

## Review Gates

The swarm uses two review layers:

- **BMAD adversarial review** runs before commit while implementation changes are still local.
- **Pre-push Bugbot / Security Review** runs after the story commit and before push, against the
  committed branch diff. If the gate applies fixes, it commits them and reruns the gate so the
  pushed diff matches the last reviewed diff; this lets the PR Bugbot run skip when the diff is
  unchanged.

In epic mode the swarm runs the pre-push gate per story for early feedback and one final time on
the full epic diff before opening the single epic PR.

## Linear Issue Creator Seam

`linear-issue-creator` is the upstream driver for Cursor plan-session work entering Linear. For
swarm-bound issues it can write a local `sprint-status.yaml` mirror row with `linear_id`,
`linear_url`, and `context_source`.

The swarm consumes that row:

- `context_source: bmad-epic` means Phase 1 creates the developer story from BMAD planning
  artifacts.
- `context_source: linear-issue` means Phase 1 fetches the Linear issue body and uses it as the
  primary story source.

If a Linear-enabled swarm reaches Phase 0.25 and the active story has no `linear_id`, the swarm
can invoke `linear-issue-creator` to backfill one issue and update the mirror row. That autonomous
path is allowed only when every creation gate resolves deterministically; otherwise the swarm
stops and reports the blocker.

## Safe upgrade model

Versioned shared core + repo-local profile. When updating from upstream:
1. Replace the managed skill files from `vixxo-copilot/agent-skills`.
2. Preserve the consuming repo's `local/profile.yaml`.
3. Review `config/profile-schema.yaml` for schema changes.

If a team needs behavior the profile cannot express, propose it upstream instead of patching
the local skill core.
