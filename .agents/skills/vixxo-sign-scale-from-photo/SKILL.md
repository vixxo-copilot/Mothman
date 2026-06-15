---
name: vixxo-sign-scale-from-photo
description: >-
  Estimates sign dimensions from storefront or fascia photos, produces red-line
  dimension overlays (PNG + PDF), and supports dual-axis panel scaling for mockups
  on building photos. Handles channel-letter storefronts (door/parking reference)
  and white-panel fascia mockups (LifeCare, Select Medical, etc.). Use when the
  user asks to measure a sign from a photo, scale letters from an image, add
  dimension lines, or tune panel height/width on a sign mockup.
---

# Sign scale from photo

Two modes:

1. **Reference scaling** — channel letters / logos on a wall; one known field
   dimension (door height, stall width, etc.).
2. **Fascia panel mockup** — white rectangular panel composited on a building
   photo; dual-axis anchors for panel height **and** width; red-line overlay
   deliverables.

Photo scale is an **estimate**, not fabrication proof.

## When to use

- "Measure this sign from the photo"
- "Add dimension lines to the sign mockup"
- "Scale the letters — door is 7 feet"
- User iterates: "make it taller", "width is good, decrease height"
- LifeCare / Select Medical / hospital fascia mockups on porte-cochère photos

## What this skill does NOT do

- Does not replace a field survey or tape measure.
- Does not send outbound messages.
- Does not modify Smartsheet, SharePoint, or SR records unless asked.

## Dependencies

- **Read** — inspect the photo.
- **Shell** — run scripts under `scripts/` (Pillow + numpy for panel mode).
- Optional: Smartsheet / SharePoint standards lookup when matching brand tiers.

## Reference files

- [`reference-dimensions.md`](./reference-dimensions.md) — default reference sizes.
- [`output-template.md`](./output-template.md) — reference-scaling packet.
- [`dimension-overlay-template.md`](./dimension-overlay-template.md) — mockup overlay packet.

---

## Mode A — Fascia panel mockup (preferred for composited signs)

Use when a **white panel** is visible on the building fascia (mockup or installed
cabinet) and the user wants a dimension table plus red-line overlay.

### Workflow

```
Task progress:
- [ ] 1. Detect panel + graphic ink in photo
- [ ] 2. Set panel height and width anchors (dual-axis)
- [ ] 3. Run measure_panel_sign.py
- [ ] 4. Tune anchors from user feedback
- [ ] 5. Emit dimension packet + deliver PNG/PDF
```

### 1. Anchors (dual-axis)

Set **two independent anchors**:

| Anchor | Controls | Example |
|--------|----------|---------|
| `panel_height` | All vertical dimensions | `4'-3"` |
| `panel_width` | All horizontal dimensions | `10'-0"` |

**Iteration rules** (from field use):

- "Width is good" → hold `panel_width`; adjust `panel_height` only.
- "Height too small / too large" → move `panel_height`; do not change width unless asked.
- "4' is too small" → do not go below ~4'-0"; prefer `4'-3"` between `4'-0"` and `4'-6"`.
- Increase height **or** decrease height independently of width — never uniform scale when user names one axis.

### 2. Run the script

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/measure_panel_sign.py \
  --image <photo> \
  --panel-height "4'-3\"" \
  --panel-width "10'-0\"" \
  --out-png tmp/<slug>-sign-dimensions.png \
  --out-pdf ~/Desktop/<slug>-sign-dimensions.pdf
```

Add `--json` for structured output.

### 3. Overlay conventions

- Red rectangle: panel face.
- Bottom horizontal: **panel width**.
- Right vertical: **panel height**.
- Optional right-side callout on primary top-line letters.
- White label boxes behind dimension text; Arial Bold 15–16 px.

### 4. Element detection notes

- **White panel:** RGB > (220, 230, 240) in upper fascia band.
- **Brand ink:** teal/green `(r<50, g>60, b>50)`.
- **Tagline ink:** neutral gray/black on panel.
- Split **two text rows** at the widest vertical gap in the middle third of panel ink.
- Split **logo / primary / tagline** by x-cluster gaps on each row.

Rename elements in the chat table to match the sign (e.g. "Select", "SPECIALTY HOSPITAL").

### 5. Emit packet

Fill [`dimension-overlay-template.md`](./dimension-overlay-template.md).

---

## Mode B — Reference scaling (channel letters, angled storefronts)

Use when scaling from a **known reference** on the wall plane (door, window, etc.).

### Angled photos — homography (preferred)

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/measure_facade.py \
  --image <photo> \
  --door <TL> <TR> <BR> <BL> \
  --door-width "6'" --door-height "7'" \
  --sign <left-top> <right-top> <left-bottom> <right-bottom>
```

### Flat quick estimate

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/scale_from_reference.py \
  --ref-pixels <REF_PX> \
  --ref-size "7'" \
  --target letter_height:<PX> \
  --target sign_overall_width:<PX> \
  --tolerance-pct 8
```

Emit [`output-template.md`](./output-template.md). Match client standard tiers via
[`reference-dimensions.md`](./reference-dimensions.md).

---

## Measurement discipline

- Height reference → height targets only (unless dual-axis mockup mode).
- State pixel edges used and detection caveats.
- Widen tolerance to **12–15%** on angled or low-res photos.
- Never fabricate dimensions the pixels do not support.

## Example — Select Medical mockup @ 4'-3" × 10'-0"

```bash
python3 .agents/skills/vixxo-sign-scale-from-photo/scripts/measure_panel_sign.py \
  --image assets/select-medical-mockup.png \
  --panel-height "4'-3\"" \
  --panel-width "10'-0\"" \
  --out-png tmp/select-medical-sign-dimensions.png \
  --out-pdf ~/Desktop/select-medical-sign-dimensions.pdf
```

Typical output band after user tuning: panel **4'-3" H × 10'-0" W**; primary
lines ~7–8½" cap height; taglines ~4½–5½" cap height.
