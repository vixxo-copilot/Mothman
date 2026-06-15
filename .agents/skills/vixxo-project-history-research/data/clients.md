# Client folder map

Authoritative per-client configuration for the
`vixxo-project-history-research` skill. The skill reads this file when:

- **Resolving a client name** the user typed (Mode 1, 2, 3, 4, 5 — Step 1).
- **Fuzzy-matching a project folder name** against existing children
  (the match cascade in `SKILL.md`).
- **Constructing a new folder name** for the create modes (Modes 4 & 5)
  using the client's modal naming pattern.
- **Filtering junk** (templates, archives, old folders) out of candidate
  lists.

The companion file `folder-structures.md` is the human-readable narrative
of why each client looks the way it does. This file is the
machine-readable spec the skill actually consumes.

## Quick lookup — name → item ID

For fast resolution. The detailed config for each client lives below.


| Client (exact folder name) | Item ID                              | Status                                                      |
| -------------------------- | ------------------------------------ | ----------------------------------------------------------- |
| Sally Beauty               | `01GSUI65XKVTX4PTGJNRBKEGP3SLOPDMXP` | Confirmed.                                                  |
| Christian Brothers         | `01GSUI65XEBBQYHFICXB32W7BHPRH5R37L` | Sampled 2026-04-23; ID cached 2026-04-28 (CBA Woodlands run). Sites/ child: `01GSUI65VK5KELO37H4NZLSPZN2BCBDKBA` (531 projects). |
| Extra Space Storage        | `01GSUI65RIL74XDNVO6B23RJA2DOFPAEGQ` | Sampled 2026-04-23; ID cached 2026-04-28 (3,279 projects, flat structure). Note: also a duplicate `ExtraSpaceStorage` folder exists (`01GSUI65SJ27OODHCGAZY3RAOKXVZTDM6C`, 3,145 projects) — investigate which is current before relying on either. |
| Rent A Center              | `01GSUI65T6IQULBP2PM5HI3IJGGBN3T2L7` | Sampled 2026-04-28 (RAC 02932 Ripley run). 23 root children, projects under `Sites/` child `01GSUI65U2QUIYBV5VSZ22E2LTRFR4RMAQ` (728 projects). |


All other clients: not yet sampled. When you encounter one, add a quick
lookup row + a full config section below, then update
`folder-structures.md` with any structural notes worth remembering.

## How to add a new client

1. From the New L Drive folder, run `list-folder-files` and grab the
   client folder's `id`. Add a row to the Quick lookup table.
2. Sample 20–40 child folder names (more if the client is messy). Note
   any subfolder layer (e.g., `Sites/`), the dominant naming style, and
   any obvious junk patterns.
3. Add a config section below using the template at the bottom of this
   file.
4. If the client has a structurally interesting wrinkle (multi-brand
   subfolders, address-based names, archived sub-trees), add a short
   note to `folder-structures.md`.

---

## Per-client config

Each section has the same shape. Fields:

- **Aliases** — phrases a user might type that should resolve to this
  client. Match case-insensitively, ignore punctuation, allow each token
  to appear in any order.
- **Structure** — one of:
  - `flat` — projects are direct children of the client folder.
  - `sites_subfolder` — projects live one level deeper, under a
    `Sites/` (or similarly named) folder.
  - `subbrand_subfolder` — projects live under per-brand subfolders
    (e.g., `Smile Brands/Bright Now Dental/`).
- **Modal naming pattern** — the most common shape for a *new* folder
  name. Used by Modes 4 & 5 to construct proposed names. Tokens:
  `{id}`, `{id:04d}` (zero-padded to 4), `{city}`, `{st}`, `{addr}`,
  `{extra}`.
- **Naming variants** — regexes (priority order, first match wins) used
  to *parse* existing folder names so they can be matched against user
  input. Use named groups: `id`, `city`, `st`, `addr`, `extra`.
- **Junk patterns** — case-insensitive substrings that mark a child
  folder as "not a real project" (templates, archives, deleted markers,
  back-office stuff). Filter these out of candidate lists.
- **Standard subfolder template** — almost always the 14 canonical
  subfolders from `SKILL.md`. Override here only if a client has
  documented variants.
- **Last verified** — date of last sampling. Re-sample if > 6 months
  old or if you start seeing unfamiliar shapes.

---

### Sally Beauty

- **Aliases:** `sally`, `sally beauty`, `sb`
- **Structure:** `flat`
- **Modal naming pattern:** `Sally{id}`
- **Naming variants** (priority order):
  1. `^Sally(?P<id>\d{3,6})$` — modal
  2. `^Sally\s+(?P<id>\d{3,6})$` — modal with stray space
  3. `^(?P<id>\d{3,6})$` — bare digits (rare; promote to `Sally{id}`
     when proposing)
- **Junk patterns:** `template`, `_old`, `archive`, `do not use`,
  `delete`, `test`
- **Standard subfolder template:** 14 canonical subfolders.
- **Last verified:** 2026-04-23 (Sally10124 confirmed during deliverable
  PDF run).

---

### Christian Brothers

- **Aliases:** `cb`, `christian brothers`, `christian brothers auto`,
  `christian brothers automotive`, `cba`
- **Structure:** `sites_subfolder` — projects live under
  `Christian Brothers/Sites/`. Always add the `Sites/` step when listing
  candidates or creating new folders.
- **Modal naming pattern:** `{id:04d} - {city}, {st}`
- **Naming variants** (priority order):
  1. `^(?P<id>\d{3,4})\s*-\s*(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})(?:\s*-\s*(?P<extra>.+))?$`
     — modal, optional trailing descriptor (e.g.,
     `0177 - Humble, TX - Fall Creek`)
  2. `^(?P<id>\d{3,4}),\s*(?P<addr>.+)$` — address-only
     (e.g., `0096, {addr}`); use when a city wasn't known
     at folder-creation time
  3. `^(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` — legacy (no id),
     pre-numbering convention; tolerate but warn when matched
- **Junk patterns:** `template`, `_old`, `_archive`, `archive`, `OLD`,
  `do not use`, `delete`, `test`, `kickoff template`
- **Standard subfolder template:** 14 canonical subfolders.
- **Last verified:** 2026-04-23.

---

### Rent A Center

- **Aliases:** `rac`, `rent a center`, `rent-a-center`, `rentacenter`
- **Structure:** `sites_subfolder` — projects live under
  `Rent A Center/Sites/`. The root folder also contains brand-asset
  PDFs, banner files, photo dumps, and per-vendor catalogs that look
  like projects but are not — be aggressive with junk filtering.
- **Modal naming pattern:** `{id:05d} {city}, {st}` (5-digit
  zero-padded id; matches the existing `02932 Ripley, WV` shape).
- **Naming variants** (priority order):
  1. `^(?P<id>\d{4,5})\s+(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` — modal
     (zero-padded or unpadded)
  2. `^(?P<id>\d{4,5})\s*-\s*(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` —
     dash-separated variant
  3. `^(?P<extra>\d-\d{10})$` — SR-numbered discovery iteration (e.g.,
     `1-5984561484`); used as a child of the project folder, not as a
     project folder name itself
  4. `^(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` — legacy (no id)
- **Junk patterns** (case-insensitive substrings — many of these are
  cross-cutting brand/reference assets at the client root, not project
  folders): `template`, `_old`, `archive`, `do not use`, `delete`,
  `test`, `0 0 0`, `000_`, `pricing`, `sign standards`, `led layouts`,
  `night photos`, `redo-`, `homechoice`, `graphic standards`,
  `billing`, `status report`, `invoice`, `banner.pdf`, `letter
  layouts`, `.pdf`, `.docx`, `.xlsx`, `.zip`
- **Standard subfolder template:** 14 canonical subfolders. *(Some
  legacy iterations use a non-standard 6-folder layout — `Pics`,
  `Quotes`, `Survey & Artwork` — for SR-numbered discovery work; do
  not normalize, treat as legitimate.)*
- **Last verified:** 2026-04-28 (RAC 02932 Ripley run).

---

### Extra Space Storage

- **Aliases:** `ess`, `extra space`, `extra space storage`,
  `extra-space`
- **Structure:** `flat`
- **Modal naming pattern:** `{id} {city}, {st}`
  (note: most existing folders are missing the space after the comma —
  `{id} {city},{st}` — but the modal *for new creation* should include
  the space for readability)
- **Naming variants** (priority order):
  1. `^(?P<id>\d{2,5})\s+(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` — modal
     (with or without space after comma)
  2. `^(?P<id>\d{2,5})\s*-\s*(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` —
     dash-separated variant
  3. `^(?P<city>[^,]+),\s*(?P<st>[A-Z]{2})$` — legacy (no id)
- **Junk patterns:** `template`, `_old`, `archive`, `do not use`,
  `delete`, `test`
- **Standard subfolder template:** 14 canonical subfolders.
- **Last verified:** 2026-04-23.

---

## Template — copy when adding a new client

```
### {Client display name (must match SharePoint folder exactly)}

- **Aliases:** `...`, `...`
- **Structure:** `flat` | `sites_subfolder` | `subbrand_subfolder`
- **Modal naming pattern:** `...`
- **Naming variants** (priority order):
  1. `^...$` — description
  2. `^...$` — description
- **Junk patterns:** `...`, `...`
- **Standard subfolder template:** 14 canonical subfolders. *(or
  document any client-specific deviations)*
- **Last verified:** YYYY-MM-DD.
```

---

## Drive / site reference (do not duplicate elsewhere)

These belong in `SKILL.md`. Linked here only for cross-reference:

- Site: `vixxo.sharepoint.com/sites/VixxoSignLighting`
- Drive (Shared Documents): `b!mH_hJO5alE-AvutIOImhpkdHB25X00xHirWbk4ejWSAkn2z2REgVTbm6ZMFdID_h`
- New L Drive folder item ID: *(resolve once and record in SKILL.md)*
