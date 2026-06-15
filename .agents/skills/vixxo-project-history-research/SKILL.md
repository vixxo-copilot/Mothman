---
name: vixxo-project-history-research
description: >-
  Researches and provisions Sign & Lighting project folders in the SharePoint
  "New L Drive" using the Microsoft 365 MCP. Use this skill when the user asks
  for a project history summary, kickoff brief, prior-job research,
  completion-doc QC review, wants to find / inventory artwork, POs, completion
  photos, estimates, surveys, or other project files for a given
  client + store / asset / SO number, OR asks to create a new project folder
  (single or batch) using the client's standard layout. Five modes:
  "history" (default — pre-project research; iteration subfolders + scope
  signals as bullet lists, not run-on sentences; **always renders a
  three-section combined PDF — history brief, completion photos, and the
  latest artwork PDF — and uploads it to the SharePoint project root,
  returning the download link**), "qc" (post-project completion
  review), "deliverable" (build a single combined PDF — summary page +
  selected artifacts — and upload it back to the project root), "create" (one
  new project folder + 14 standard subfolders, two-step confirm), and
  "batch-create" (many new project folders in one go, two-step confirm,
  replaces the legacy n8n folder-creation workflow).
---

# Project History Research

Pulls structured intelligence from — and provisions new folders into — the
SharePoint "New L Drive" via the `microsoft-365` MCP server
(`@softeria/ms-365-mcp-server`). Replaces ad-hoc folder spelunking
**and** the legacy n8n folder-creation workflow with a repeatable
five-mode workflow.

## When to use

Trigger this skill when the user says any of:

- "history on store 12345" / "what's been done at this site"
- "kickoff brief for [project / SO / store]"
- "pull the past artwork / POs / photos for ..."
- "QC review for ..." / "completion docs for ..."
- "summarize the L Drive folder for ..."
- "find the latest [art / estimate / survey] for ..."
- references a Sally Beauty / Cosmo / etc. store number, asset number, or SO
number with a research-shaped question
- "create a project folder for ..." / "set up a new folder for ..." /
"provision the standard folders for ..."
- "create folders for these ..." / "bulk create" / "batch create" /
pastes a list of new sites that need folder structure

## Critical setup (do this once before first run)

### 1. Fix the mcp.json — `--org-mode` is required for SharePoint

The current `microsoft-365` entry only enables personal-account tools
(OneDrive, Outlook, etc.). SharePoint Sites tools require `--org-mode`. In
`.cursor/mcp.json`, the `microsoft-365` server should be:

```json
"microsoft-365": {
  "command": "npx",
  "args": [
    "-y",
    "@softeria/ms-365-mcp-server@latest",
    "--org-mode"
  ]
}
```

After saving, fully reload the MCP server (Cursor → Settings → MCP →
disable/enable, or restart Cursor).

### 2. One-time login

In the chat, ask the agent to call the `login` tool. Follow the device-code
URL + code in the browser. Confirm with `verify-login`. Tokens cache to the
OS credential store, so this is a one-time step per machine.

### 3. Confirm reachability of the L Drive

Have the agent call `get-sharepoint-site-by-path` with the site path
`/sites/VixxoSignLighting` (see Reference Data below) to confirm access.
If it returns 403, ask IT to grant `Sites.Read.All` (and
`Sites.ReadWrite.All` if you want this skill to write files later).

### 4. Local synced New L Drive root (required for History / QC brief file output)

History (Mode 1) and QC (Mode 2) markdown outputs are written **into the
resolved SharePoint project folder’s local OneDrive path** so they appear
next to job files and sync back to SharePoint like any other document.

Set a **machine or session environment variable**:

| Variable | Value (example — adjust for your PC / sync name) |
| -------- | ------------------------------------------------ |
| `VIXXO_NEW_L_DRIVE_LOCAL` | `C:\Users\PCardinal\OneDrive - Vixxo\Vixxo Sign & Lighting - New L Drive` |

Rules for the agent:

1. **Strip** a trailing `\` from the env value.
2. **Append** the same path segments as under SharePoint `New L Drive`,
   using **exact** Graph folder `name` values (match `data/clients.md`
   client folder spelling).
   - **`flat`** (e.g. Sally Beauty):  
     `{VIXXO_NEW_L_DRIVE_LOCAL}\{Client folder name}\{Project folder name}\`
   - **`sites_subfolder`** (e.g. Christian Brothers, Rent A Center):  
     `{VIXXO_NEW_L_DRIVE_LOCAL}\{Client folder name}\Sites\{Project folder name}\`  
     (use the configured subfolder name from `data/clients.md` when it is
     not literally `Sites` — it usually is.)
   - **`subbrand_subfolder`:** include every brand / intermediate segment
     exactly as on SharePoint under that client.
3. **Filename:** `{client-slug}-{store-id}-{YYYY-MM-DD}-history.md` (Mode 1)
   or `...-qc.md` (Mode 2).
4. **Before write:** if `{VIXXO_NEW_L_DRIVE_LOCAL}` is unset **or** the
   computed directory does not exist, write to the legacy fallback
   `memory/projects/...` instead, and tell the user to set the
   env var and sync OneDrive so the project folder exists locally.
5. **Do not** create the client or project folder solely to drop the brief
   — if the folder is missing, use the fallback path and note that the
   project may need provisioning (Mode 4) or OneDrive sync.

User-facing summary of the saved file should give the **full absolute path**
when the brief lands under OneDrive (so they can open it in Explorer).

## Reference data

### Where "New L Drive" actually lives

`New L Drive` is **a folder inside the default Documents library** on the
Vixxo Sign & Lighting SharePoint site — it is *not* its own drive /
library. Full layout:

```
SharePoint site: vixxo.sharepoint.com/sites/VixxoSignLighting
└── Drive (document library): "Shared Documents" / "Documents"   ← drive id below
    └── Folder: "New L Drive"                                     ← item id, resolve once
        ├── Folder: "Sally Beauty"                                ← client folder
        │   └── Folder: "Sally1022222"                            ← project folder
        │       └── Folder: "Sally1022222 12.04.2024"             ← dated iteration
        │           ├── Approvals/
        │           ├── Art & EPS/
        │           ├── ... (14 canonical subfolders — see list below)
        ├── Folder: "Cosmo" (etc.)
```

Web URL of the New L Drive folder (for sanity-check / "open in browser"
links):
`https://vixxo.sharepoint.com/:f:/r/sites/VixxoSignLighting/Shared%20Documents/New%20L%20Drive`

### Site / drive identifiers (from existing n8n workflows — known good)


| Item                                   | Value                                                                | Notes                                                                                                                |
| -------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Site path                              | `/sites/VixxoSignLighting`                                           | Pass to `get-sharepoint-site-by-path`                                                                                |
| Site host                              | `vixxo.sharepoint.com`                                               | —                                                                                                                    |
| Drive ID — Shared Documents library    | `b!mH_hJO5alE-AvutIOImhpkdHB25X00xHirWbk4ejWSAkn2z2REgVTbm6ZMFdID_h` | The library that *contains* the New L Drive folder. Used in all `/drives/{drive-id}/...` calls.                      |
| Item ID — `New L Drive` folder         | `01GSUI65SKG47YKOIE6VEKZGQP3U2YYK6Z`                                 | Resolved & cached 2026-04-28 (66 client folders).                                                                    |
| Item ID — `Sally Beauty` client folder | `01GSUI65XKVTX4PTGJNRBKEGP3SLOPDMXP`                                 | Child of the New L Drive folder.                                                                                     |


If the site or drive ID ever changes (tenant migration, library rename),
re-discover with: `get-sharepoint-site-by-path` → `list-sharepoint-site-drives`
→ pick the drive whose `name` is `Documents` or `Shared Documents` →
record its `id`. Then `get-drive-root-item` + `list-folder-files` to find
the `New L Drive` child item id.

### Client → folder map + per-client config

Authoritative spec lives in `[data/clients.md](data/clients.md)`. Read
that file at the start of any run that needs to:

- Resolve a client name the user typed.
- Fuzzy-match a project folder name (Step 1 of every mode below).
- Construct a new folder name in Modes 4 / 5 (the modal naming
  pattern + variants live there).
- Filter junk folders out of candidate lists.

`[data/folder-structures.md](data/folder-structures.md)` is the
human-readable narrative companion — read it once when you're learning
the skill or onboarding a new client; you don't need it on every run.

Do **not** maintain a duplicate client map in this file.

### Standard project subfolder names (canonical list)

These are the **14** subfolders the folder-creation modes provision for
every new project. Use this same list to canonicalize names found in
the wild (e.g., "Art" → "Art & EPS", "POs" → "Purchase Orders").

```
Approvals
Art & EPS
Completion Documents
Emails
Engineering
Estimates
Financials
Freight
LED Layouts
Permits & Engineering
Purchase Orders
Sign Code- Property Documentation
Survey
Vendor Invoices
```

### File-type classifiers

When grouping files by purpose, apply rules in this order. First match wins.


| Type               | Subfolder hint                                           | Filename keywords                                               | Extensions                     |
| ------------------ | -------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------ |
| `artwork`          | Art & EPS, LED Layouts                                   | `art`, `proof`, `mock`, `eps`, `layout`                         | `.pdf .ai .eps .psd .jpg .png` |
| `purchase_order`   | Purchase Orders, Vendor Invoices                         | `po`, `purchase order`, `purchase_order`                        | `.pdf .xlsx .xls`              |
| `estimate`         | Estimates, Financials                                    | `estimate`, `quote`, `bid`, `proposal`                          | `.pdf .xlsx .xls`              |
| `completion_photo` | Completion Documents                                     | `photo`, `install`, `before`, `after`, `site`, `progress`       | `.jpg .jpeg .png .heic`        |
| `completion_doc`   | Completion Documents                                     | `signoff`, `sign-off`, `completion`, `sat`, `acceptance`, `coc` | `.pdf .docx`                   |
| `survey`           | Survey                                                   | `survey`, `field`, `measure`                                    | `.pdf .docx .xlsx`             |
| `permit`           | Permits & Engineering, Sign Code- Property Documentation | `permit`, `application`, `sign code`                            | `.pdf .docx`                   |
| `engineering`      | Engineering, LED Layouts                                 | `engineering`, `stamp`, `seal`, `calc`, `wet`                   | `.pdf .dwg`                    |
| `email`            | Emails                                                   | —                                                               | `.msg .eml .pdf`               |


### Year detection (for grouping multi-year history)

Use this regex against folder names: `/\b(20[1-9]\d)\b/`. If no year is in
the folder name, fall back to the folder's `createdDateTime`. If the two
disagree by more than 1 year, prefer `createdDateTime` and note the
mismatch in the output.

## Project folder identification (input normalization + match cascade)

Every mode in this skill starts the same way: the user gives you a
client name + some kind of project identifier, and you have to map that
to a real SharePoint folder (Modes 1–3) or decide that no such folder
exists and a new one should be proposed (Modes 4–5).

Users type loose. "sally #10124", "Sally10124", "10124 sally beauty",
"CB 158 Katy", "ess158 carrollton", "extra space 158", "158 carrollton
TX" — all of those should resolve cleanly. Christian Brothers folders
live under a `Sites/` subfolder; Extra Space Storage often omits the
space after the comma; Sally Beauty embeds the id with no separator.
This section is the single algorithm for handling all of that.

### Step A — Normalize the user input

1. Strip leading/trailing whitespace.
2. Lowercase a working copy (keep the original for display).
3. Strip punctuation noise: `#`, `_`, `.`, `:`, double spaces. **Do
   not** strip commas (they're meaningful in `City, ST`).
4. Tokenize on whitespace. Pull apart tokens that mash an alpha prefix
   onto a digit run (`sally10124` → `sally`, `10124`; `ess158` →
   `ess`, `158`).
5. Identify candidate fields:
   - **id token:** any pure-digit token (3–6 chars).
   - **state token:** any 2-char alpha token in `[A-Z]{2}` (after
     uppercasing).
   - **city token(s):** alpha tokens that aren't an alias hit and
     aren't a state.
   - **alias tokens:** anything that matches an alias from
     `data/clients.md`.

### Step B — Resolve the client

Match alias tokens (case-insensitive, ignoring order) against the
Aliases list of every client in `data/clients.md`. Exact-substring hits
beat fuzzy hits. If:

- **Exactly one client matches** — proceed with its config.
- **Zero clients match** — ask the user explicitly which client. Do
  not guess.
- **Multiple clients match** — present the candidates and ask. Do not
  guess.

Cache the resolved client + its config for the rest of the session.

### Step C — Locate the project candidate list

1. Resolve the client folder item ID (from the Quick lookup table in
   `clients.md`; resolve and cache if missing).
2. If the client's `Structure` is `sites_subfolder`, drill one level
   deeper into the configured subfolder (`Sites/`, etc.) before
   listing.
3. If `subbrand_subfolder`, ask the user which brand if not implied.
4. `list-folder-files` and capture the children. Drop any whose name
   matches a `Junk patterns` substring.
5. For each remaining child, run the client's `Naming variants`
   regexes in priority order. The first match wins; record the parsed
   `id` / `city` / `st` / `addr` / `extra` fields alongside the
   raw name.

### Step D — Match cascade

Run these in order. **Stop at the first layer that yields a single
high-confidence hit.**

1. **Exact match (post-normalize)** — user's normalized id == parsed
   `id` of exactly one child. Done.
2. **Field match** — user's `id` + (city OR state) match one child's
   parsed fields. Done.
3. **Substring contains** — user's id (or city) appears as a substring
   in exactly one child's raw name. Done.
4. **Fuzzy** — Levenshtein ≤ 2 against either the raw name or the
   parsed `{id} {city}` reconstruction; or token-set ratio ≥ 90.
   Surface the top 3 matches and ask the user to pick.
5. **No match** — fall through to Step E.

When multiple children tie at the same layer, never auto-pick. Present
a numbered list (name, `webUrl`, `lastModifiedDateTime`,
`parentReference.path`) and ask the user to choose.

### Step E — No match: did-you-mean + offer to create

When the cascade returns nothing, show:

1. The five closest names (lowest Levenshtein against the user's
   tokens), with their `webUrl` and last-modified date. "Did you mean
   one of these?"
2. The constructed proposed name using the client's
   `Modal naming pattern` (e.g., for the user input "158 carrollton
   tx" against Extra Space Storage: propose `158 Carrollton, TX`).
3. An offer to **create** that proposed folder + the 14 standard
   subfolders. Hand off to **Mode 4** if the user accepts. Use the
   two-step confirmation described there.

If the user input is too sparse to construct a proposal (e.g., they
only gave a client and an id with no city), ask for the missing
fields before offering Mode 4.

### Implementation note

For batch input (Mode 5) the LLM will typically generate a one-off
Python script that reads `data/clients.md`, applies the normalization +
regexes, and produces the preflight table. Same algorithm, just
vectorized. Keep the script in `memory/projects/.batch_{slug}/` and
delete it after the audit report is written, mirroring the Mode 3
cleanup discipline.

---

## Mode detection


| Signal in user's message                                                                                              | Mode                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| "kickoff", "history", "what's been done", "prior projects", "research"                                                | **history** (default)                                                                                                                           |
| "QC", "closeout", "completion review", "post-install", "wrap-up"                                                      | **qc**                                                                                                                                          |
| "combined PDF", "one PDF", "package up", "deliverable", "send-out pack", "merge POs / photos / artwork into one file" | **deliverable**                                                                                                                                 |
| "create folder", "new project folder", "set up the standard folders", "provision a folder for ..."                    | **create**                                                                                                                                      |
| "create folders for these ...", "bulk create", "batch create", or pastes a multi-line list of new sites               | **batch-create**                                                                                                                                |
| Ambiguous                                                                                                             | Ask: "History brief, QC review, combined deliverable PDF, create one new project folder, or batch-create folders for a list of new locations?" |


---

## Mode 1: History brief (default)

Goal: at the start of a new project, give the PM a 1–2 page narrative of
prior work at the same store / asset, plus a categorized inventory of
documents they may want to reference. **Within each iteration,** present
subfolder counts and headline scope as **markdown bullet lists** (one line
per folder / fact) — see Step 4 item 3 — **never** as one comma-packed
sentence.

### Step 1 — Identify the project folder

Required input from the user (ask if missing): **client name** + **store
number / asset ID / SO number / search keyword**.

Run the algorithm in
**[Project folder identification](#project-folder-identification-input-normalization--match-cascade)**
above (Steps A–D). It handles:

- Loose user input (`sally #10124`, `CB 158 katy`, etc.) via Step A
  normalization.
- Client resolution via Step B.
- Per-client structural quirks (e.g., the `Sites/` subfolder on
  Christian Brothers) via Step C.
- The exact → field → contains → fuzzy match cascade in Step D.

If the cascade returns no match (Step E), do **not** silently fall
through here — the user might have typoed the wrong client or there
might genuinely be no project folder yet. Show the did-you-mean list and
the Mode 4 create offer, then wait for direction.

If the client folder has > ~200 candidate children and listing every
one is too slow, you may pre-filter using `search-onedrive-files`
(`drive-id` = the Shared Documents drive ID, `q` = the user's
identifier), but **always re-filter results locally** to only those
whose `parentReference.path` contains `/New L Drive/{client name}/`
(plus `/Sites/` if applicable) — the drive-wide search returns hits
from anywhere in Shared Documents.

### Step 2 — Inventory the chosen project folder

For the selected project folder ID:

1. Call `list-folder-files` to enumerate immediate children.
2. Children whose names contain a 4-digit year (per the year regex above)
  are **dated job iterations**. There may be 1 (single project) or many
   (multi-year history).
3. For each dated iteration, call `list-folder-files` again to get its
  subfolders. Map subfolder names against the canonical list above.
4. For each canonical subfolder present, call `list-folder-files` once
  more to get the file list. Capture: `name`, `id`, `size`,
   `lastModifiedDateTime`, `webUrl`, and inferred classifier type (per
   the rules above).
5. Build an in-memory structure of the form:
  ```
   project = {
     name, id, webUrl,
     iterations: [
       { name, year, createdDateTime, webUrl,
         subfolders: [
           { name, file_count, last_modified, web_url,
             files: [{ name, classifier, web_url, size, modified }] }
         ]
       }
     ]
   }
  ```

Be polite to the API: if a subfolder has > 200 children, paginate with
`$top` and `@odata.nextLink`; if a project has > 5 iterations, ask the
user whether to limit to the most recent N before deep-diving.

### Step 3 — Fetch context for the narrative (optional but recommended)

For richer summaries, pull a small amount of actual content. **Only do
this on files the user is likely to care about — don't download
everything.**

For each iteration's most-recent **estimate**, **PO**, and **scope /
completion document**, call `download-onedrive-file-content` to get the
temporary download URL and either:

- For PDFs ≤ 5 pages: extract text (the model can read the URL via web
fetch).
- For larger files: skip extraction and reference by URL only.

Skip image/photo files at this stage — counts and links are enough.

### Step 3b — Pre-Production Review Smartsheet enrichment

Goal: for every iteration, surface whether the artwork was submitted
to and approved in Pre-Prod Review, the **approved Design #**, and the
**Sales Order #** — these aren't anywhere in the SharePoint folders but
are the fastest way to confirm a job actually made it through the
formal review gate.

**Sheet:** `8908088876001156` ("Pre-Production Review")
**Auth:** `SMARTSHEET_ACCESS_TOKEN` env var (Bearer token, Smartsheet
REST API v2.0).

Relevant columns (as of 2026-04-28):

| Column title | Meaning |
| --- | --- |
| `Date` | Date of submission |
| `Client` | Client display name (often abbreviated, e.g. `CBA` for Christian Brothers) |
| `Location / Project I.D.` | Location string — varies wildly (e.g., `CBA - Phoenix, AZ`, `Thunderbird/Peoria, AZ`, `0087 Woodland Hills, CA`) |
| `Base Art Number` | The base VX number (e.g., `VX1104979`) — primary lookup key |
| `Design #` | The **approved** Design # including revision (e.g., `VX1104979 R3`) |
| `Sales Order #` | The Sales Order # tied to this submission |
| `Sign Type(s)` | Channel letters / Faces / Lexan Panels / etc. |
| `Manufacturer` | Vendor (often matches the SharePoint vendor invoice filenames) |
| `Request Review` (checkbox) | Submitted to Pre-Prod Review |
| `Approved` (checkbox) | Approved |
| `Pending Approval` (checkbox) | Mid-review |
| `art@vixxo.com approval` (picklist) | Picklist status from the art team |

**Lookup procedure:**

1. For each iteration with a known latest artwork, call
   `GET /search/sheets/{sheetId}?query={base_art_number}` (e.g., search
   for `VX1104979`). The base art number is the highest-signal key.
2. If no hits on the base art number, fall back to a search by
   **client + location** (try a couple variants — e.g., `CBA - Woodlands`,
   `Woodlands TX`, `Panther Creek`). Filter the result set on
   `Client` containing the client and `Location / Project I.D.`
   containing the city/store.
3. For each matching `objectType == "row"` result, fetch the full row
   with `GET /sheets/{sheetId}/rows/{rowId}` and read the columns above.
4. If still no hits across all reasonable searches, record this as
   **"Not in Pre-Prod Review"** and surface it as a workflow gap — this
   is itself a useful signal for the next PM.

**API quirks:**

- The `search` endpoint returns max 100 hits per call and has no
  pagination. If you hit the limit on a generic term (e.g., `CBA`
  returns 100), narrow with the base art number instead.
- A single physical row often appears as multiple search hits (cells +
  attachments + discussions). Dedupe by `objectId` for `objectType ==
  "row"`.
- `displayValue` is preferred over `value` for cells — it carries the
  rendered string for picklists/contacts/dates.
- The sheet starts in 2018-01-08; pre-2018 work won't be in here.

### Step 4 — Synthesize the narrative

> **Required output sections — do not skip any.** A Mode 1 brief is only
> complete when **every** section below is present in the rendered
> markdown. The renderer will not produce the canonical PDF shape if any
> of these are missing.
>
> Required `##` headings, in order:
>
> 1. `# {Client} {store-id} — {City, ST} — Project history` (the H1
>    title — exactly one)
> 2. Project header block (bullets directly under the H1 — generated
>    date, client/store, address, project folder, iteration count,
>    latest completed tranche signal)
> 3. `## Fast-quote Part# recognition (latest completed artwork)` —
>    **only when** the client appears in
>    `../vixxo-fast-quote-builder/data/part-number-rules.md`. Omit
>    cleanly for unmapped clients. See item 2 below for required shape.
> 4. `## Iteration timeline`
> 5. `## Recurring patterns`
> 6. `## Document inventory`
> 7. `## Notes & gaps`
>
> Under `## Iteration timeline`, **every** iteration must have an h3 of
> the form `### {Year} — {iteration folder name}` and, immediately under
> that h3, **all of these** bullets, in this order:
>
> - **Subfolder inventory** — one bullet per **populated** canonical
>   subfolder, formatted `- **{Name}** — {count} ({one-line summary})`.
>   Legacy / WO-style trees use one bullet per actual child folder.
> - `- **Empty:** {comma-separated list}` (a single bullet listing empty
>   canonical subfolders; omit if the iteration has none).
> - `- **Latest art:** [{filename}]({webUrl}) ({revision}, {YYYY-MM-DD})`
>   — required even when none. If the iteration has no artwork PDF,
>   write `- **Latest art:** none on file`.
> - `- **Pre-Prod Review:** {status}` — required for every iteration.
>   Status text from Step 3b: `Submitted + Approved (Design # X, SO # Y)`,
>   `Submitted, pending`, `Submitted, not approved`, or `Not in Pre-Prod
>   Review sheet`. If the iteration pre-dates 2018-01-08, append
>   `(sheet starts 2018-01-08; pre-2018 artwork is expected absence)`.
> - `- **Headline scope signal:**` followed by sub-bullets (vendor names,
>   dollar amounts, scope keywords). **Bullets, not a comma-chained
>   paragraph.** Required for every iteration.
>
> Under `## Document inventory`, **all four** of these h3 sub-sections
> must exist, each followed by a `| Year | File | Summary |` table, even
> if a classifier has zero files across the entire project:
>
> 1. `### Artwork`
> 2. `### Purchase Orders`
> 3. `### Estimates / Financials`
> 4. `### Vendor Invoices`
>
> If a classifier genuinely has no files anywhere in the project, the
> table still exists with a single body row:
> `| — | _(no {classifier} files found across any iteration)_ | — |`.
> Do not silently omit the table.
>
> Two canonical exemplar briefs (both already in SharePoint and on the
> local OneDrive mirror) demonstrate the required shape end-to-end. Open
> whichever client matches before generating a new brief and follow the
> same shape:
>
> - `Sally Beauty / Sally10063 / sally-beauty-10063-2026-05-12-history.md`
> - `Extra Space Storage / 727 Brooklyn, NY / ess-727-brooklyn-ny-2026-05-12-history.md`

Produce a markdown summary in this order:

1. **Project header** — client, store/asset identifier, total iterations
   found, year span, link to the project folder.
2. **Fast-quote Part# recognition (latest completed artwork)** — include
   **only when** the client appears in
   `../vixxo-fast-quote-builder/data/part-number-rules.md`
   (Sally Beauty, Cosmo, CBA, ESS, UA, TLG, RAC, etc.). Skip for clients
   not yet mapped there.
   - **Pick the iteration** the PM would treat as **latest completed**
     work: prefer the most recent iteration that has **closeout signal**
     (e.g. populated `Completion Documents`) and/or the iteration whose
     artwork matches **approved Pre-Prod Design #** when Step 3b has one;
     do **not** silently use a greenfield iteration with empty completion
     if an older packaged job is clearly the last finished tranche.
   - **Artwork file:** highest-revision PDF in that iteration’s `Art & EPS/`
     (or client equivalent). Note **calendar year** from the iteration
     folder name and/or artwork metadata; note **Design #** as `VX…` +
     revision (from filename or Smartsheet).
   - **Extract text** from the artwork PDF (prefer local synced path under
     `VIXXO_NEW_L_DRIVE_LOCAL` when present; otherwise download via Graph
     and extract). Apply the same token logic as **vixxo-fast-quote-builder**:
     explicit matches on `[A-Z]{2,5}\d+[A-Z0-9]*`; if missing, **synthesize**
     Part#s using `part-number-rules.md` + `sign-type-rules.md` the way
     `build_quote.py` would (height from elevations, RACEWAY/flush, tenant
     LEXAN sq ft, etc.). Do **not** invent SKUs not justified by those rules.
   - **Sherwin-Williams / SW:** from the **same extracted text**, pull any
     paint codes tied to **channel letter / raceway / return / fascia**
     wording (e.g. `SW 7100 …`). Omit if none appear.
   - **Required output shape (minimal — no extra prose in this section):**

     ```markdown
     ## Fast-quote Part# recognition (latest completed artwork)

     **Listed from:** **{YYYY}** · iteration **{iteration folder name}**
     · design **{VXnnnnnn R#}** — [artwork PDF]({webUrl}).

     - **{Part#}**
     - **{Part#}**
     - **SW {####}**
     ```

     Use only **bold bullets** for each distinct Part# (and each SW code).
     Do **not** embed sign-type labels, parser commentary, markdown tables,
     rule-trace columns, or Smartsheet recap inside this section — those
     belong elsewhere in the narrative if needed.
   - If PDF text cannot be read or the client has no part-number mapping,
     **omit** this section (or replace with one line: part# list unavailable).
3. **Iteration timeline** — bullet list, oldest → newest:
   - `YYYY` — *iteration name* — what subfolders are populated, headline
   scope (one sentence inferred from estimate / scope doc if available),
   vendor names if visible, total file count.
   - **Subfolder inventory:** use a **bullet list**, not one long sentence.
     One bullet per populated canonical subfolder (`**Name** — count /
     summary`). Put **empty** subfolders on a separate short list or a
     single `**Empty:** …` line. **Legacy / WO-style** trees (not the 14
     template): one bullet per subfolder with `(empty)`, link to nested
     folder, or one-line note (e.g. *billing note only*).
   - **Headline scope signal:** when describing vendors / POs / permit /
     survey / financial artifacts for that iteration, use **bullets** (one
     fact per line), not a comma-chained paragraph.
   - **Always cite the latest artwork from that iteration by filename
   with a clickable link** (e.g., `[VX1104979 ... .pdf](sharepoint url)`).
   Pick the highest-revision / newest-modified file in `Art & EPS/`
   (or client equivalent). If the iteration has no artwork, say so
   explicitly.
   - **Always cite the Pre-Prod Review status** for that iteration's
   artwork (per Step 3b lookup): one of `Submitted + Approved (Design
   # X, SO # Y)`, `Submitted, pending`, `Submitted, not approved`, or
   `Not in Pre-Prod Review sheet` (the last is itself a workflow flag
   worth surfacing).
4. **Recurring patterns** — any repeated vendors, repeated complaints,
   recurring scope items across iterations. If none, say so.
5. **Document inventory** — one table per classifier (Artwork, Purchase
   Orders, Estimates / Financials, Vendor Invoices), rows ordered by year
   desc. Use the column shape:
   - **All four tables:** `| Year | File | Summary |`. Iteration is
     already obvious from Year, so collapse it into the Summary instead
     of carrying a separate Iteration column. (If a project genuinely has
     two iterations *in the same year* and the distinction matters,
     promote Iteration back to its own column on that one table only:
     `| Year | Iteration | File | Summary |`.)
   - The **File** column is itself the clickable markdown link to the
     SharePoint `webUrl` (`[{filename}]({webUrl})`). There is **no**
     separate `Link` column.
   - The **Summary** column is **1–2 sentences sourced from the actual
     document content**, not a restatement of the filename. For PDFs,
     open them locally (the project folder syncs to OneDrive under
     `VIXXO_NEW_L_DRIVE_LOCAL`) with `pypdf` and pull:
     - **total dollar amount** — look for `Total Value:` first, then
       fall back to the first `\$\d{1,3}(,\d{3})*(\.\d{2})?` regex
       match in the extracted text;
     - **date(s)** on the document;
     - **vendor / installer name** (Coast2Coast, Ally, SCA, etc.);
     - **scope keywords** — survey, permit, install, manufacture,
       channel letter, tenant panel, vinyl, fabricate, remove, replace;
     - **PM / contact** when present.
     Keep summaries specific (vendor + dollars + scope) — do **not**
     write generic "purchase order document" filler.
   - When a row points at a **folder** rather than a single file (e.g.
     `Coast 2 Coast (4 add'l)` or a `Financials folder` aggregate row),
     the Summary should describe the folder's contents in aggregate
     (file count, total size, what they cover) instead of pretending to
     summarize one document.

   Layout note: the renderer
   (`scripts/render_combined_pdf.py`) renders **all** markdown tables at
   **8pt cell / 8pt bold header** with `repeatRows=1`, so 1–2 sentence
   Summary cells fit cleanly and the header re-appears on every page if
   a table spills.

Do **not** add a "Suggested next actions" / "Recommendations" section.
The PM owns the next-action call; this skill stays evidence-only.

### Step 4.5 — Pre-render checklist (do not render an incomplete brief)

Before invoking the renderer in Step 5, verify the markdown you just
wrote against the Required output sections checklist at the top of
Step 4. Specifically confirm, in this order:

1. The H1 title is present and follows the
   `# {Client} {store-id} — {City, ST} — Project history` shape.
2. The project header bullet block (generated date, client/store,
   address, project folder, iteration count, latest-tranche signal)
   appears immediately under the H1.
3. The Fast-quote Part# recognition section is present **iff** the
   client is mapped in
   `vixxo-fast-quote-builder/data/part-number-rules.md`. If unmapped,
   the section is cleanly omitted — not a stub.
4. `## Iteration timeline` exists. Every iteration h3 under it has
   **all five** required bullets (Subfolder inventory, optional Empty,
   Latest art, Pre-Prod Review, Headline scope signal). No iteration
   is missing any of these.
5. `## Recurring patterns` exists. If the project genuinely has none,
   the section still exists and explicitly says so.
6. `## Document inventory` exists and contains **all four** h3
   sub-sections (`### Artwork`, `### Purchase Orders`,
   `### Estimates / Financials`, `### Vendor Invoices`), each with
   a `| Year | File | Summary |` table that has at least one body row
   (or the documented "no files found" placeholder row).
7. `## Notes & gaps` exists.

If any check fails, **return to Step 4 and complete the missing
section before rendering.** Do not call `render_combined_pdf.py` on
an incomplete brief. The renderer will faithfully render whatever
markdown it receives, including the absence of inventory tables — it
cannot rescue a brief that was never fully written.

### Step 5 — Save the brief (markdown + combined PDF, both required)

History briefs **always** produce two artifacts:

1. A **local markdown file** dropped in the synced project folder so it
   syncs back to SharePoint with the rest of the project files.
2. A **combined PDF deliverable uploaded to the SharePoint project root**
   in the canonical three-section shape (history brief → latest artwork
   PDF → completion photo thumbnails). The PDF webUrl is the headline
   link returned to the user.

#### 5a. Write the markdown

Write the brief (full narrative + inventory table) to **the local synced
project parent folder** — the directory that mirrors SharePoint
`New L Drive/.../{project folder}/` — using **`VIXXO_NEW_L_DRIVE_LOCAL`**
and the path-segment rules in **Critical setup §4**.

```
{VIXXO_NEW_L_DRIVE_LOCAL}\…\under New L Drive…\{Project folder name}\{client-slug}-{store-id}-{YYYY-MM-DD}-history.md
```

If §4’s directory is unavailable, fall back to:

```
memory/projects/{client-slug}-{store-id}-{YYYY-MM-DD}-history.md
```

#### 5b. Render the combined-PDF deliverable

The PDF is a **single combined deliverable** with three concatenated
sections in this fixed order:

```
Section A — Project history brief (rendered from the markdown above).
            First line on page 1 is the literal banner:
            "Section A - Project history brief (from markdown). "
            "Section B: latest artwork PDF. "
            "Section C: completion photo thumbnails (4 per page)."

Section B — The latest revision artwork PDF appended verbatim.

Section C — Completion photo thumbnails laid out 4 per page in a 2x2
            grid (~1/4 page each). Each thumbnail has the filename as
            a small label underneath. EXIF rotation is respected.
```

Source files are picked by these deterministic rules (so two runs on
the same project produce the same PDF):

- **Section A markdown** — the file written in §5a.
- **Section B artwork** — the highest-revision PDF in the latest
  iteration's `Art & EPS/` folder (or the per-client equivalent — see
  `data/folder-structures.md`). If the latest iteration has no PDF
  artwork, fall back to the most recent earlier iteration that does.
  If no iteration has any PDF artwork, **omit Section B** and note
  "no artwork PDF available" in the user-facing summary.
- **Section C photos** — every image (`*.jpg`, `*.jpeg`, `*.png`,
  `*.heic`) inside the **latest iteration's `Completion Documents/`**
  folder, sorted alphabetically by filename. If the latest iteration
  has no photos, fall back to the most recent earlier iteration that
  does. If no iteration has any completion photos, **omit Section C**
  (do not invent placeholder tiles) and note "no completion photos
  available" in the user-facing summary.

**Use the permanent renderer** (do not regenerate render code per run):

```
.agents/skills/vixxo-project-history-research/scripts/render_combined_pdf.py
```

Drive it with a small JSON manifest under
`memory/projects/.history_{client-slug}-{store-id}/render_manifest.json`
with these keys (all paths absolute):

```jsonc
{
  "markdown":           "abs/path/to/{stem}-history.md",
  "output":             "abs/path/to/{stem}-history.pdf",
  "section_a_header":   null,                 // null → use the default banner
  "completion_photos":  ["abs/path/photo1.jpg", "abs/path/photo2.jpg"],
  "artwork_pdf":        "abs/path/to/latest-artwork.pdf"
}
```

Then invoke the renderer (use the **`py` launcher** per Peter's IT
guidance — `python` may resolve to the wrong interpreter on this box):

```
py .agents\skills\vixxo-project-history-research\scripts\render_combined_pdf.py --manifest memory\projects\.history_{slug}\render_manifest.json
```

The renderer prints a JSON line on stdout with `output`, a `page_counts`
object (`{section_a, artwork, section_c, total}`), and the resolved
photo/artwork inputs. It writes directly to the manifest's `output`
path, so the combined PDF lands at:

```
{VIXXO_NEW_L_DRIVE_LOCAL}\…\{Project folder name}\{client-slug}-{store-id}-{YYYY-MM-DD}-history.pdf
```

(Or `memory/projects/…-history.pdf` when §4 fallback is in use.)

Renderer dependencies (verified available on Peter's box, 2026-05-12):
**`reportlab` 4.x**, **`pypdf` 6.x**, **`Pillow` 11.x**, and
**`markdown` 3.x**. This workspace does **not** have pandoc,
weasyprint, xhtml2pdf, or wkhtmltopdf — do not try to install them.

#### 5c. Land the PDF on the SharePoint project root

Goal: the PDF must exist in the SharePoint **project root** folder
(same folder as the project iterations — **not** any iteration
subfolder) and you must have its `webUrl` before reporting back to the
user.

There are two paths, **prefer the first when available**:

**Path A — OneDrive-sync fast path (when §5a wrote under
`VIXXO_NEW_L_DRIVE_LOCAL`):**

1. The local synced project folder is a OneDrive mirror of the
   SharePoint folder. Writing the PDF to disk is the upload —
   OneDrive sync pushes it back to SharePoint automatically.
2. After writing the PDF, **verify the sync landed it** before
   reporting: call `list-folder-files` on the project folder's
   `driveItemId` and look for a child whose `name` matches the PDF
   filename. Match the local file's byte size against the listing's
   `size` to confirm the upload completed (not a 0-byte placeholder).
3. If the file appears with matching size, record its `webUrl` — this
   is the headline link. Skip explicit MCP upload entirely.
4. If the file does not appear (or appears with size 0) after the
   first listing, wait ~10 s and re-list once. Sync is usually well
   under that. If it still hasn't landed, fall through to Path B —
   sync may be paused or the folder may not actually be synced.

**Path B — explicit MCP upload (Path A unavailable or failed):**

Combined PDFs commonly run **5–15 MB** because they embed the artwork
PDF plus install-photo thumbnails. Plan the upload accordingly:

1. For small outputs (≤ 4 MB — only happens when the iteration has no
   artwork PDF and no completion photos), call **`upload-file-content`**
   with the project folder's `driveItemId` as the parent and the PDF
   body as a base64 string. `conflictBehavior` should be `"replace"`
   so re-running the skill the same day overwrites cleanly with
   version history preserved.
2. For the typical case (> 4 MB), use the Mode 3
   `create-upload-session` pathway and honor the API quirks documented
   in Mode 3 Step 6 (especially the `driveItemId` = file-target trap;
   use the parent-folder-then-rename recovery pattern if the upload
   lands as a sibling of the project folder).
3. If `VIXXO_NEW_L_DRIVE_LOCAL` was unavailable and the markdown went
   to `memory/projects/…`, this path is mandatory — locate the
   SharePoint project folder's `driveItemId` from the Step 1 match
   cascade and use it as the parent. Do **not** skip the upload just
   because OneDrive sync is missing locally.
4. Use the returned `driveItem.webUrl` as the headline link.

#### 5d. Clean up + report to the user

- Delete the helper directory
  `memory/projects/.history_{client-slug}-{store-id}/` after the upload
  succeeds (mirrors Mode 3 and Mode 5 cleanup discipline). Keep the
  local markdown + PDF copies under `VIXXO_NEW_L_DRIVE_LOCAL` — they
  are the working artifacts.
- The user-facing summary must include, in this order:
  1. **PDF download link** — render the SharePoint `webUrl` as a
     clickable markdown link with the PDF filename as label
     (`[{client-slug}-{store-id}-{YYYY-MM-DD}-history.pdf]({webUrl})`).
     This is the headline deliverable.
  2. **Local file paths** — absolute paths to both the `.md` and
     `.pdf` files so the user can open them in Explorer.
  3. The headline findings (existing summary content).

Offer the `outlook-email-formatter` skill if the user wants to share the
brief via email; the PDF webUrl is normally enough by itself.

---

## Mode 2: QC review pack

Goal: at the end of a project, verify completion documentation is
present and complete, and produce a QC checklist for review.

### Step 1 — Identify the **current** project iteration

Same as History mode Step 1, but the user is pointing at a project
that's just wrapped. Default to the **most recently modified** iteration
folder if multiple exist.

### Step 2 — Enumerate completion artifacts

For the current iteration:

1. `list-folder-files` on the iteration root.
2. Drill into these subfolders specifically: `Completion Documents`,
  `Approvals`, `Purchase Orders`, `Vendor Invoices`, `Financials`.
3. Classify each file using the rule table above. Capture counts per
  classifier.

### Step 3 — Build the QC checklist

Output structure:

```
## QC Checklist — {client} / {store-id} / {iteration name}

### Completion documentation
- [{x or space}] Signed completion / acceptance form  ({n} found, {filename + link} or "MISSING")
- [{x or space}] Install photos                       ({n} photos in {subfolder})
- [{x or space}] Final invoice from vendor            ({filename + link} or "MISSING")
- [{x or space}] Permit closeout                      (...)
- [{x or space}] Approvals on file                    (...)

### Financial reconciliation
- Estimate total: ${...}        (from {filename})
- PO total:       ${...}        (from {filename})
- Invoice total:  ${...}        (from {filename})
- Variance:       ${...}        (FLAG if > 5%)

### Anomalies / things to confirm
- {bullet per finding}
```

The financial section requires opening the relevant docs (download URL +
extract). If extraction is unavailable, leave the totals as `?` and note
"open manually".

### Step 4 — Save & route

Write to the **local synced project parent folder** via
**`VIXXO_NEW_L_DRIVE_LOCAL`** (Critical setup §4), filename
`{client-slug}-{store-id}-{YYYY-MM-DD}-qc.md`. If that path cannot be used,
fall back to `memory/projects/{client-slug}-{store-id}-{YYYY-MM-DD}-qc.md`.

Then ask whether to:

- Email the QC checklist to a reviewer (use `outlook-email-formatter`)
- Log a Linear issue for any MISSING items (use `linear-issue-manager`,
routed to the relevant team)
- Both

Wait for explicit confirmation before any external write.

---

## Mode 3: Combined deliverable PDF

Goal: produce a single self-contained PDF that a PM, vendor, or stakeholder
can open or email — first page is a project summary, then selected
artifacts merged in a deliberate order. Upload it back to SharePoint at the
**project root** so it's discoverable alongside the iteration folders.

Always run Mode 1 (history brief) implicitly first to gather the inventory
— the deliverable's summary page is built from that data.

### Step 1 — Confirm contents with the user

Default contents (state these and ask "ok or adjust?"):

1. **Page 1**: programmatic summary page (project header, iteration
  timeline, recurring patterns, quick links — see Step 3).
2. **All Purchase Orders** (chronological, oldest → newest, across all
  iterations).
3. **Completion photos from the latest iteration's Completion Documents
  folder** (one photo per page, with a header label).
4. **Latest artwork PDF** (highest revision found in `Art & EPS` of the
  latest iteration that has art).

Common adjustments to expect: include vendor invoices, include all
artwork revisions (not just latest), include the survey PDF, restrict
photos to a specific iteration, change page order. Confirm before
building — re-doing a 3MB upload is slow.

### Step 2 — Pull source files

For each artifact in the agreed contents list:

1. Call `download-onedrive-file-content` with `driveId` + `driveItemId`
  (no `format` param — see "API quirks" below).
2. The response contains a temporary download URL. Fetch the bytes
  with a plain HTTP GET to a local scratch directory:
   `memory/projects/.build_{slug}/`.
3. Cache by item ID so a second pass doesn't re-download.

Skip files > ~10 MB unless the user explicitly asked for them — the
combined PDF gets big fast.

### Step 3 — Build the summary page (page 1)

Generate a single-page PDF with `reportlab.platypus.SimpleDocTemplate`
(letter, ~0.5–0.6" margins). Include:

- Project name + store address + iteration count + brief date.
- Project folder hyperlink (clickable in the PDF).
- **Quick links section** — clickable hyperlinks to any folders worth
  highlighting:
  - **Survey folder(s)** for any iteration that has one (the user
   specifically wants these surfaced).
  - Each iteration folder.
  - Any other classifier folder the contents discussion flagged
   (e.g., LED Layouts).
- **Latest artwork by iteration** — for every iteration, list the
  newest / highest-revision artwork file from that iteration's
  `Art & EPS/` folder (or client equivalent) as a clickable hyperlink
  showing the **full filename** (e.g., `VX1104979 CHRISTIAN BROS
  Woodlands, TX.pdf`). Render as a labeled list or a 2-column table
  (`Iteration | Latest art file (linked)`). If an iteration has no
  artwork, say so explicitly. This is required even when the merged
  PDF only embeds the single newest artwork, so the reader can locate
  earlier-iteration art in one click.
- **Pre-Prod Review status by iteration** — render a table with
  columns `Iteration | Pre-Prod submitted? | Approved? | Approved
  Design # | Sales Order #` populated from the Smartsheet lookup in
  Step 3b. If a row is missing, mark the cells `—` and add a footnote
  `Not in Pre-Prod Review sheet`. This is required for every Mode 3
  deliverable, even when no rows are found, because absence is itself
  evidence (the project skipped the review gate).
- 1–2 sentence narrative per iteration (scope, vendor, value).
- Recurring patterns (3–5 bullets, copied from the history brief).
- For projects with a single canonical estimate / quote, a compact
  line-item table is nice-to-have.

Use `<a href="{url}" color="#0563C1"><u>label</u></a>` for the in-PDF
hyperlinks. URL-encode SharePoint paths (`%20` for spaces, `%23` for
`#`).

### Step 4 — Convert non-PDF artifacts

JPGs / PNGs need converting before merge. Open with Pillow, drop onto a
letter-sized canvas via `reportlab.pdfgen.canvas`, fit-to-page with a
small top-margin label like `"Completion photo - rear sign (installed
Aug 2021)"`. One photo per page.

### Step 5 — Merge in the agreed order

Use `pypdf.PdfWriter`. Order matters and should match what the user
confirmed in Step 1. Default ordering:

```
[summary page]
[PO 1, PO 2, ... POn]            # chronological
[photo 1 (page), photo 2, ...]   # latest iteration only by default
[artwork PDF]                     # last revision
```

Write to `memory/projects/{ProjectName}-combined-{YYYY-MM-DD}.pdf`.
Verify final page count and size before uploading.

### Step 6 — Upload to SharePoint (project root, **not** iteration folder)

Default destination is the **project root folder** (e.g.,
`Sally Beauty/Sally10124/`), not any year-specific iteration folder.
The user will almost always want it at the project root so it's not
buried.

1. If a file with the target name already exists at the destination:
  - Look it up (`list-folder-files` with `filter: "name eq '...'"`).
  - Call `create-upload-session` against **that file's `driveItemId`**
   with `body: { item: { "@microsoft.graph.conflictBehavior":
   "replace" } }`. This overwrites cleanly and preserves version
   history.
2. If no existing file:
  - Call `create-upload-session` against the **parent folder's
   `driveItemId`** with `body: { item: { "@microsoft.graph.name":
   "{filename}.pdf", "@microsoft.graph.conflictBehavior": "rename" } }`.
3. Take the returned `uploadUrl` and PUT the file in chunks (see "API
  quirks" below for chunk size + headers).
4. The final chunk's response (HTTP 200/201) contains the new
  `driveItem` — confirm `name`, `size`, and `parentReference.path`
   match expectations. If the name picked up a `" 1"` suffix, a stale
   placeholder existed — fix with `move-rename-onedrive-item`.

### Step 7 — Cleanup

- Delete the scratch directory `memory/projects/.build_{slug}/`.
- Delete any one-off build / upload helper scripts.
- Keep the local copy of the combined PDF (
  `memory/projects/{ProjectName}-combined-{YYYY-MM-DD}.pdf`) and the
  history brief markdown — both are useful working artifacts.
- Tell the user the SharePoint `webUrl` of the uploaded file.

### API quirks (learned the hard way)

- `download-onedrive-file-content` with `format: "pdf"` returns
  **`406 Not Acceptable / InputFormatNotSupported`** even for files
  that are already PDFs. Just omit the `format` parameter — the
  response gives you a direct download URL regardless.
- Upload session chunks must be a multiple of **320 KiB**. A 1.25 MiB
  chunk (`320 * 1024 * 4`) is a good default — large enough to be
  fast, small enough to recover from a stalled chunk. Always set
  `Content-Length` and `Content-Range: bytes {start}-{end}/{total}`.
- A naïve single-PUT of the entire file body via PowerShell pipelines
  tends to stall on multi-MB files. Use `urllib.request` from a
  Python helper script with a 60–120s per-chunk timeout and a
  progress print per chunk.
- Upload sessions expire (~15 min). If a session times out mid-upload,
  call `create-upload-session` again to get a fresh `uploadUrl`
  rather than retrying the old one.
- `conflictBehavior: "rename"` against an existing zero-byte
  placeholder will silently produce `"{name} 1.pdf"`. Prefer
  `"replace"` when the intent is to update an existing artifact.
- **`create-upload-session` `driveItemId` is the file target, NOT
  the parent folder.** This is the most expensive trap in the whole
  Mode 3 flow. If you pass the project-folder driveItemId as
  `driveItemId` and put the desired filename in
  `body.item.@microsoft.graph.name`, the MCP treats the folder
  itself as the upload target and will create the file as a *sibling*
  of the project folder (with the project folder&apos;s name suffixed
  ` 1`), ignoring your requested filename entirely. Two correct
  patterns:
  - **New file at parent root:** find or create a placeholder file
    inside the parent folder first, then call `create-upload-session`
    against that file&apos;s `driveItemId` with `conflictBehavior:
    "replace"`. Or, easier: do the upload against the parent folder
    and then immediately fix it with `move-rename-onedrive-item`
    (see next bullet).
  - **Replace existing file:** look up the existing file&apos;s
    `driveItemId` with `list-folder-files` filter, then call
    `create-upload-session` against *that* with
    `conflictBehavior: "replace"`. This is the well-behaved path and
    matches the SKILL.md Step 6 description.
- **Recovery:** if the upload landed at the wrong path / with the
  wrong name (the sibling-with-suffix bug above), use
  `move-rename-onedrive-item` to set both `body.name` (correct
  filename) and `body.parentReference.id` (target folder
  driveItemId) in a single call. The MCP server happily accepts both
  in one PATCH and the file moves cleanly with version history
  intact. Do **not** delete and re-upload — the cycle wastes the
  upload session and re-downloads source artifacts.

---

## Mode 4: Create a new project folder (single)

Goal: provision **one** new project folder under the correct client (and
the correct `Sites/` / sub-brand subfolder if applicable), populated with
the 14 standard subfolders. Replaces the legacy n8n folder-creation
workflow for one-off creation.

This mode is the only sanctioned destination of "no match — offer to
create" from the match cascade (Step E above), and it is also a
top-level entry point when the user explicitly says "create a folder
for ...".

### Step 1 — Confirm the inputs

You need:

- The **resolved client** (from cascade Step B).
- A **proposed folder name** constructed from the client's
  `Modal naming pattern` and the parsed user input (cascade Step E).
- The **parent folder item ID** — the client folder, plus the
  `Sites/` (or sub-brand) child if the client's structure requires it.

Show the user, in one block:

```
Create new project folder?

Client:        {Client display name}
Parent path:   /New L Drive/{client}/[Sites/...]
Folder name:   {proposed name}
Subfolders:    14 standard (Approvals, Art & EPS, Completion Documents,
               Emails, Engineering, Estimates, Financials, Freight,
               LED Layouts, Permits & Engineering, Purchase Orders,
               Sign Code- Property Documentation, Survey, Vendor Invoices)

Reply:
- "confirm" to proceed
- "rename to ..." to change the folder name
- "cancel"
```

Wait for explicit `confirm`. This is **the first step** of the two-step
confirmation.

### Step 2 — Preflight check

After the user types `confirm`:

1. `list-folder-files` on the parent and look for a child whose name
   exactly matches the proposed name (after normalization). If one
   exists, **stop**. Show the existing folder's `webUrl` and ask
   whether the user wants to (a) cancel, (b) use the existing folder
   (and run history mode against it), or (c) provide a different
   name.
2. Also run the match cascade fuzzy layer one more time against this
   parent's children, in case a near-duplicate exists with a slightly
   different name. If matches with Levenshtein ≤ 2, surface them and
   ask the user to confirm they really want a new folder.

If the preflight is clean, show:

```
Preflight OK. No conflicts at:
  /New L Drive/{client}/[Sites/]/{proposed name}

Reply "go" to create the folder + 14 subfolders, or "cancel".
```

Wait for explicit `go`. This is **the second step**.

### Step 3 — Create

1. Create the project folder under the parent (use the MCP's
   create-folder tool; if none is exposed, POST to
   `/drives/{drive-id}/items/{parent-id}/children` with
   `{ "name": "{proposed name}", "folder": {},
   "@microsoft.graph.conflictBehavior": "fail" }`). `fail` is
   intentional — preflight already said it didn't exist, so a
   conflict here means a race and we want to abort, not silently
   rename.
2. For each of the 14 standard subfolder names, create as a child of
   the new project folder. Same `conflictBehavior: "fail"` for
   idempotency safety.
3. If any single subfolder creation fails, capture the error but keep
   going — the project folder itself is the important part. Report
   any failures at the end.

### Step 4 — Confirm + report

Output to the user:

```
Created: {proposed name}
URL:     {webUrl of the new folder}

Subfolders provisioned (14/14):
  ✓ Approvals
  ✓ Art & EPS
  ... etc.

Errors: none
```

Replace `(14/14)` with whatever actually succeeded. List any errors
explicitly with the subfolder name + reason.

Do **not** automatically run history mode against the new (empty) folder
— the user knows it's new. Offer to switch to history mode only if the
preflight surfaced a near-duplicate they ended up using instead.

---

## Mode 5: Batch create project folders

Goal: provision **many** new project folders in a single, auditable run.
Replaces the legacy n8n bulk-create flow that handled lists of up to ~80
new sites per submission.

This mode is **purely folder-creation**. Any other side effects the old
n8n workflow performed (Smartsheet rows, Linear issues, notifications)
are out of scope here — handle them in their own dedicated skills (e.g.,
`linear-issue-manager`) after this one finishes.

Naming uses the **hybrid pattern strategy**: each row in the user's
input is parsed independently against the client's full set of
`Naming variants` (any of which is considered legitimate), but every row
that *cannot* be cleanly parsed by any variant gets normalized to the
client's **modal naming pattern** before creation. The user can override
per-row in the preflight.

### Step 1 — Collect input

Accept any of:

- A pasted list, one project per line.
- A `.txt` / `.csv` / `.md` filename to read.
- An inline mini-table.

Per-line freeform format. The skill should be tolerant of:

```
158 carrollton tx
158 Carrollton, TX
ess 158 carrollton, tx
158, Carrollton, TX
```

If the user hasn't already named the client, ask for it once at the top
of the batch (a single batch is one client at a time — do not mix).

**Hard cap: 200 rows per batch.** If the user pastes more, refuse
politely and ask them to split. This protects against runaway runs and
keeps the audit report manageable.

### Step 2 — Build the preflight table

Generate a one-off helper script in
`memory/projects/.batch_{client-slug}_{YYYY-MM-DD}/preflight.py` that:

1. Reads `data/clients.md` (the per-client config).
2. Calls `list-folder-files` against the parent folder once and caches
   the existing children + their parsed fields.
3. For each input row, runs Step A normalization + Step C parsing +
   Step D match cascade.
4. Constructs the proposed final folder name using the modal pattern
   when no variant cleanly parses, or preserving the row's existing
   shape when a non-modal variant is a clean match (this is the
   "hybrid" behavior).
5. Emits a markdown table with one row per input line and a status
   column.

Status values:

| Status    | Meaning                                                                  | What the skill does next                              |
| --------- | ------------------------------------------------------------------------ | ----------------------------------------------------- |
| `OK`      | Parses cleanly, no existing folder matches, name is well-formed.         | Will create on confirm.                               |
| `DUPE`    | A folder with the proposed name already exists at the parent.            | Skip on confirm. User may override to "use existing". |
| `NEAR`    | A folder with Levenshtein ≤ 2 to the proposed name exists.               | Show both names. User must `keep`, `merge`, or `drop` before confirm. |
| `ASK`     | Multiple parse interpretations or missing required fields (e.g., no st). | User must clarify before confirm.                     |
| `INVALID` | Fails all variants and the modal pattern can't be filled.                | Drop unless user provides corrected text.             |

Render the preflight table inline. Example column set:

```
#  | Input                | Parsed (id/city/st)   | Proposed name        | Status | Notes
1  | 158 carrollton tx    | 158 / Carrollton / TX | 158 Carrollton, TX   | OK     |
2  | 159 katy tx          | 159 / Katy / TX       | 159 Katy, TX         | NEAR   | Existing: "159 Katy,TX" (Lev 1)
3  | foo bar              | (none)                | (cannot construct)   | INVALID|
```

Save the table also to
`memory/projects/.batch_{client-slug}_{YYYY-MM-DD}/preflight.md` so the
user has a stable reference.

### Step 3 — User review (first confirmation step)

Offer this menu:

```
Reply with one of:

- "edit row N: ..."  to change the proposed name (or any parsed field)
                     for row N.
- "drop row N"       to remove a row from the batch.
- "add ..."          to append more rows.
- "merge row N"      (NEAR rows only) to use the existing folder
                     instead of creating a new one.
- "preview"          to redisplay the preflight table.
- "confirm"          to lock the batch and move to final confirmation.
- "cancel"           to abandon.
```

Apply each edit in order; redisplay the preflight after each change so
the user always sees the current state. Loop until the user types
`confirm` or `cancel`. **No creation has happened yet.**

When the user confirms, recompute statuses one last time (the parent
folder might have changed since Step 2 — re-list it). Surface any new
DUPE/NEAR results before moving on.

### Step 4 — Final confirmation (second step)

Show a final summary before any write:

```
Ready to create {N} folders under:
  /New L Drive/{client}/[Sites/]/

Will create:
  - {proposed name 1}
  - {proposed name 2}
  ...

Will skip ({M} dupes):
  - {existing 1}
  ...

Each folder gets the 14 standard subfolders.

Reply "go" to execute, or "cancel" to abort.
```

Wait for explicit `go`. **Until you see `go`, do not call any
create-folder tool.** This is the second of the two confirmation steps.

### Step 5 — Execute

Use the same one-off helper script directory
(`memory/projects/.batch_{client-slug}_{YYYY-MM-DD}/`) for an executor
script (`create.py`) that:

1. Iterates the OK rows.
2. For each, creates the project folder, then the 14 subfolders.
3. Uses `conflictBehavior: "fail"` everywhere — preflight is
   authoritative; a conflict at this stage is an error, not a silent
   rename.
4. Concurrency: limit to **4 folders in flight at a time**. SharePoint
   tolerates this comfortably; higher concurrency starts triggering
   `429 Too Many Requests`.
5. Backoff: on `429` or `5xx`, exponential backoff starting at 2s,
   doubling, max 60s, max 6 retries per call. On `Retry-After` header
   present, honor it.
6. Idempotency: if a project folder happens to already exist when
   Step 5 hits it (race, or a manual user action between confirm and
   execute), capture the existing item and instead verify each of the
   14 subfolders exists; create the missing ones. Mark the row as
   `RECONCILED` in the report.

### Step 6 — Audit report

Write the final outcome to:

```
memory/projects/{YYYY-MM-DD}-batch-{client-slug}.md
```

Structure:

```
# Batch folder creation — {Client} — {YYYY-MM-DD}

- Submitted: {N} rows
- Created:   {N_created}
- Skipped:   {N_skipped} (existing duplicates)
- Reconciled:{N_reconciled} (missing subfolders backfilled)
- Errors:    {N_errors}

## Per-row outcomes

| #  | Proposed name        | Status     | Folder URL | Subfolders | Notes |
| -- | -------------------- | ---------- | ---------- | ---------- | ----- |
| 1  | 158 Carrollton, TX   | CREATED    | {webUrl}   | 14/14      |       |
| 2  | 159 Katy, TX         | RECONCILED | {webUrl}   | 13/14      | "Survey" already existed; left alone. |
| 3  | foo bar              | SKIPPED    | -          | -          | INVALID at preflight; never attempted. |

## Errors

- {row #}: {full error text}
```

### Step 7 — Cleanup

- Delete `memory/projects/.batch_{client-slug}_{YYYY-MM-DD}/` (the
  helper scripts + preflight markdown).
- Keep the audit report (`{YYYY-MM-DD}-batch-{client-slug}.md`).
- Tell the user the audit report path + the parent folder `webUrl` so
  they can spot-check.

Do not auto-trigger any side effects (no Linear issues, no Smartsheet
rows, no notifications). If the user wants those, point them at the
appropriate skill.

---

## Output format guidance (history + qc modes)

- Save History/QC markdown to the **synced project folder** when
  `VIXXO_NEW_L_DRIVE_LOCAL` resolves (Critical setup §4); report that full
  path. Use `memory/projects/...` only as the documented fallback.
- **History mode (Mode 1) also renders a combined PDF deliverable
  (Section A history brief + Section B latest artwork PDF +
  Section C completion photo thumbnails, 4 per page) and uploads it to
  the SharePoint project root** (see Mode 1 Step 5b/5c). The
  user-facing summary must lead with a clickable markdown link to the
  uploaded PDF's `webUrl`, then list the absolute paths of the local
  `.md` and `.pdf` copies, and explicitly note the three-section
  page-count breakdown in section order (e.g., "16 pages: 3 brief +
  5 artwork + 8 photos"). Do not bury the PDF link below the
  findings.
- Always include the project folder `webUrl` near the top so the user can
one-click into SharePoint.
- **Fast-quote Part# block (Mode 1):** When present, use **only** the
  `Listed from:` line (year · iteration folder name · Design # + artwork
  link) and a **short bullet list** of Part#s and `SW ####` paint codes.
  No tables or parser essay in that section — see Mode 1 Step 4 item 2.
- **Mode 1 canonical shape is mandatory.** Every Mode 1 brief must
  satisfy the Required output sections checklist at the top of Step 4
  (H1 + project header + optional Fast-quote Part# + Iteration timeline
  with all five per-iteration bullets per iteration + Recurring patterns
  + Document inventory with all four `| Year | File | Summary |`
  sub-tables + Notes & gaps). Step 4.5 is the pre-render gate. Two
  approved exemplars on SharePoint set the canonical shape: Sally10063
  and Extra Space Storage 727 Brooklyn.
- File references are `[{filename}]({webUrl})` — never raw item IDs in
user-facing output.
- Group long file lists by year, then by classifier.
- If a section is empty, say so explicitly ("No POs found in 2024
iteration") rather than omitting the section silently.
- **Iteration timeline (Mode 1):** subfolder inventories and headline
  scope signals must use **bullet lists** (see Mode 1 Step 4 item 3),
  not run-on comma sentences.
- Keep narratives tight — bullets over paragraphs.

## Tool-call discipline

- Before invoking any `microsoft-365` tool the first time in a session,
confirm authentication with `verify-login`. If it fails, instruct the
user to run `login` and retry.
- Cache discovered IDs (drive id, client folder ids, project folder id)
as in-conversation context — don't re-look-them-up between steps.
- Use `$select` and `$top` on list calls when supported to keep responses
small. The MCP server respects `MS365_MCP_MAX_TOP` if set.
- Prefer `list-folder-files` (one folder) over `search-query` (whole
tenant) unless you genuinely need cross-folder search — search-query
is rate-limited and returns less metadata.
- **Mode 1 (history) is a sanctioned upload path** for exactly one
artifact: the rendered combined-PDF deliverable (`{client-slug}-
{store-id}-{YYYY-MM-DD}-history.pdf` — Section A history brief +
Section B latest artwork PDF + Section C completion photo thumbnails,
see Mode 1 Step 5b), uploaded to the SharePoint project root and
nowhere else. It may rely on the OneDrive-sync fast path (writing
under `VIXXO_NEW_L_DRIVE_LOCAL` and verifying via `list-folder-files`),
or it may call `create-upload-session` against the project folder's
`driveItemId` with `conflictBehavior: "replace"` (the typical
explicit-upload path because combined PDFs commonly run 5–15 MB), or —
in the rare ≤ 4 MB case where Section B and Section C are both empty —
`upload-file-content`. It must **never** call any `delete-*` tool,
never upload anything other than that one combined PDF, and never
write into an iteration subfolder.
- **Mode 2 (qc) is read-only.** Never call `delete-onedrive-file`,
`delete-drive-item-permission`, `delete-sharepoint-list-item`,
`move-rename-onedrive-item`, or any upload/create tool from this
mode.
- **Mode 3 (deliverable) is a sanctioned upload path.** It may call
`create-upload-session`, perform PUT uploads against the returned
`uploadUrl`, and use `move-rename-onedrive-item` to correct an
auto-renamed file. It must **never** call any `delete-*` tool. Always
confirm the destination folder + filename + conflict behavior with the
user before the first PUT.
- **Modes 4 (create) and 5 (batch-create) are the sanctioned
folder-creation paths.** They may create folder children via the
MCP's create-folder tool (or POST `/drives/{drive-id}/items/{parent}/
children` with `{ "folder": {} }`). They must **never** call any
`delete-*` tool, never call `move-rename-onedrive-item`, and never
upload files. They must use `conflictBehavior: "fail"` at the actual
write step (the preflight is authoritative). They must complete both
confirmation steps before the first create call.

## Guardrails

- Do not fabricate file names, vendor names, dollar amounts, or
iteration history. If a value isn't in the data returned by the MCP,
mark it as unknown.
- Do not embed absolute paths from `parentReference.path` in
user-facing prose — they're noisy. Use `webUrl` instead.
- Do not write the SharePoint drive ID, item IDs, or any access tokens
into the saved brief / QC file. Internal IDs stay internal.
- Folder *creation* is owned by Modes 4 and 5 and uses the 14
canonical subfolders. The legacy n8n folder-creation workflow is
deprecated — do not hand off to it; route to Mode 4 / 5 instead.
- Mode 1 (history) uploads **exactly one** PDF per run — the rendered
combined deliverable described in Mode 1 Step 5b (Section A brief +
Section B latest artwork PDF + Section C completion photo thumbnails,
named `{client-slug}-{store-id}-{YYYY-MM-DD}-history.pdf`) — to the
**project root** folder, never an iteration subfolder, never any
other filename, and never as separate per-section files.
- A Mode 1 brief that is missing any of the Required output sections
  (Step 4 checklist) or fails the Step 4.5 pre-render check is
  **incomplete**, not "minimal". Do not paper over by rendering
  early. Fix the markdown, then render.
- Uploading a single combined deliverable PDF is allowed under Mode 3
only, and only to the project root folder unless the user explicitly
asks otherwise. Do not push individual artifacts (POs, photos,
artwork) into iteration subfolders from this skill.
- Modes 4 and 5 must complete **both** confirmation steps before any
write. A single "yes" is not enough — the user must explicitly type
the second confirmation token (`go`) after seeing the preflight.
- Modes 4 and 5 are pure folder creation. Do not create Linear issues,
Smartsheet rows, calendar events, notifications, or any other side
effect from this skill — those belong in their own dedicated skills
and the user can chain them after this one finishes.
- Batch creation is hard-capped at **200 rows**. If the user supplies
more, ask them to split rather than silently truncating.
- If file counts in a single iteration exceed ~500, ask the user whether
to sample (most-recent N per classifier) before pulling everything.

## Edge cases

- **No matching project found** — follow the cascade Step E: surface
the 5 closest candidate names (with `webUrl` and last-modified) AND
the constructed proposal under the client's modal naming pattern AND
offer to switch to Mode 4 to create it. Don't pick one of those
options for the user; let them choose.
- **Project folder exists but no dated iterations inside** — treat the
project folder itself as the single iteration.
- **Iteration names without a year** — use `createdDateTime` year and
flag in the output ("year inferred from created date").
- **Subfolder name doesn't match canonical list** — include it under a
separate "Non-standard subfolders" section in the inventory; do not
silently drop.
- **Permission denied on a subfolder** — note it in output ("Access
denied: Financials") rather than failing the whole run.
- **Multiple clients in a single store query** (e.g., user just types
"13767") — list candidates from each client folder and ask which to
pick.

## Future extensions (not built yet)

- Auto-extract scope text from estimates / quotes for richer narrative
- Photo thumbnails inline (Graph supports thumbnail URLs)
- Cross-iteration vendor/cost comparison tables
- Webhook-driven QC triggers (Smartsheet checkbox → run this skill)
- Mode 3: pre-built reusable Python helper module (build_summary.py,
upload_session.py) instead of writing one-off scripts each run
- Mode 3: optional "shareable link" generation (Graph
`createLink`) so the upload step also returns a copyable
read-only link for vendors
- Mode 5: optional rollback — if execution fails midway, undo the
already-created folders. Currently the audit report flags partial
state and asks the user to clean up manually.
- Backfill `data/clients.md` with the remaining high-volume clients
(CubeSmart, Public Storage, Dollar Tree, Smile Brands, Select
Medical) — each needs a sampling pass before its config can be
trusted in batch mode.
- Per-client subfolder template overrides (in `data/clients.md`) for
the rare client that needs a 13- or 15-folder layout instead of the
canonical 14.

