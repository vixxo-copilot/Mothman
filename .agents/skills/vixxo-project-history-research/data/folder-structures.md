# Client folder structures — human reference

This file is the narrative companion to `clients.md`. It exists so that a
new agent (human or LLM) can quickly understand *why* the New L Drive
looks the way it does before diving into the regex tables.

The machine-readable spec lives in `clients.md`. If you change anything
structural here, mirror it there.

## How clients organize their projects (cross-cutting patterns)

### Pattern A — Flat, ID-prefixed

`{Client}/{IdToken} {Optional location}/`

The default and most common pattern. The first segment of the project
folder name is a stable site / store / asset identifier; everything
after it is descriptive and may drift.

Examples:

- `Sally Beauty/Sally10124/`
- `Extra Space Storage/158 Carrollton, TX/`

Use this when there is no per-region or per-brand subdivision and every
project is a single physical site.

### Pattern B — Sites subfolder

`{Client}/Sites/{IdToken} - {City}, {ST}/`

A `Sites/` (occasionally `Stores/`, `Locations/`) folder sits between
the client and the project. Often introduced when the client folder
also holds non-project content (templates, training, vendor specs).

Examples:

- `Christian Brothers/Sites/0158 - Katy, TX - Fulshear/`
- `Christian Brothers/Sites/0177 - Humble, TX/`
- `Christian Brothers/Sites/Abilene, TX/` *(legacy)*

When this pattern is in play, the skill **must** drill into the
`Sites/` subfolder before doing any project-name matching, and **must**
include `Sites/` in the path when creating new project folders.

### Pattern C — Sub-brand subfolder

`{Client}/{Brand}/{Project}/`

Holding-company clients with multiple consumer brands (Smile Brands,
Select Medical) split projects by brand first. Resolution requires
either an explicit brand from the user or asking which brand applies.

Not yet sampled in this skill — placeholder for when first encountered.

## Naming style observations

### Identifier conventions vary

- **Sally Beauty:** identifier embedded in the folder name with no
  separator (`Sally10124`).
- **Christian Brothers:** zero-padded 4-digit id, dash-separated from
  city (`0158 - Katy, TX`). Earlier folders used no id at all.
- **Extra Space Storage:** unpadded 2–4 digit id, space-separated from
  city, comma-separated state — **but the comma often has no trailing
  space** (`158 Carrollton,TX`). New folders the skill creates should
  include the space (`158 Carrollton, TX`) — readability over historical
  fidelity.

### Legacy migrations are common

Most clients have a tail of pre-numbering folders that don't fit the
modern pattern. They're real projects, not junk — match them with the
"legacy" regex variants in `clients.md`, but warn the user when the
match is via a legacy pattern so they can confirm.

### Junk and templates

Every client has a few of: `_old`, `_archive`, `template`,
`kickoff template`, `do not use`, `_DELETE`, `TEST`. Filter these from
candidate lists by default. Only surface them if the user's query
explicitly contains one of those tokens.

## When to re-sample a client

Re-run the sampling procedure if:

- The "Last verified" date in `clients.md` is more than 6 months old,
  or
- You see folder names that don't match any of the documented variants
  (could indicate the client adopted a new convention), or
- A client is restructured (e.g., adopts a `Sites/` subfolder).

## Sampling procedure

1. `list-folder-files` on the client folder. Note whether you see a
   `Sites/`, `Stores/`, or per-brand subfolder layer.
2. If yes, `list-folder-files` one level deeper.
3. Eyeball 20–40 folder names. Group them by visual similarity. The
   biggest group is the modal pattern; smaller groups are variants.
4. Note any obviously non-project folders (templates, archives) and
   add them to the junk patterns list.
5. Update `clients.md` (the per-client config section) and bump the
   `Last verified` date.

## Open questions

- **Cosmo Prof, Beauty Systems Group, Armstrong McCall** — Sally
  Beauty's sister brands. Are they separate top-level client folders or
  nested under `Sally Beauty`? Sample on next encounter.
- **Public Storage vs Extra Space** — both self-storage; do they share
  any structural conventions? Worth comparing once both are sampled.
- **Multi-tenant sites** (e.g., a strip mall with two clients): are
  these duplicated under each client folder, or cross-referenced? No
  examples seen yet.
