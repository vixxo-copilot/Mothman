# Reference dimensions for photo scaling

Use when the user does not supply a known measurement. **Always prefer a
user-confirmed dimension** over these defaults.

## How to pick a reference

1. Choose an object on the **same image plane** as the sign (same wall face).
2. Measure the **same axis** for reference and target (height-to-height or
   width-to-width). Do not mix axes.
3. Measure **outermost usable edges** consistently (e.g., door head to sill,
   not just glass).
4. Prefer references that span a large share of the frame — small references
   amplify error.

## Common references (verify on site when possible)

| Object | Typical size | Notes |
|--------|--------------|-------|
| Commercial entry door (single) | 3'-0" x 6'-8" or 3'-0" x 7'-0" | Measure jamb to jamb, head to sill |
| Commercial double door | 6'-0" x 6'-8" or 6'-0" x 7'-0" | Two 3'-0" leaves |
| Storefront door (user override) | **Ask user** | Example: 7'-0" height |
| Standard parking space width | 9'-0" | Striping centerline to centerline |
| Concrete parking stop | ~6'-0" long | Parallel to stall |
| ADA handicap sign face | 12" x 18" | If visible and current code |
| Standard brick (face) | 2-1/4" x 7-5/8" | Course height ~2-1/4" |
| 4x8 plywood sheet | 4'-0" x 8'-0" | Temporary hoarding only |

## Pixel measurement tips

- Read the image file to get `pixelWidth` / `pixelHeight` first.
- Estimate pixel extents from the photo; state which edges you used.
- If perspective skew is obvious (camera angled up/down), call it out and widen
  the tolerance band to **12–15%**.
- When possible, take a second reference (e.g., door height **and** door
  width) and average the scale factors.

## Client standard matching

After scaling, if the user names a client/brand, compare against the design
standards sheet (Smartsheet `Design Standards Collection` or SharePoint
`00000000standards`). Match **letter height** and **overall sign width** to
the nearest standard size tier.

Example CosmoProf channel-letter tiers:

| Letter height | Typical overall width |
|---------------|----------------------|
| 12" | ~9'-1" |
| 18" | ~13'-7" |
| 24" | ~17'-11" |
| 30" | ~22'-8" |
| 36" | ~26'-11" |
