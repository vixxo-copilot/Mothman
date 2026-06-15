# Vendor Quote Tracker — Examples

## Example: full status check

**User:** Check on all vendor emails

**Agent actions:**
1. `verify-login`
2. `list-mail-folder-messages` → `sentitems`, top 50
3. Inbox search for vendor domains + Storage Star subjects
4. `get-mail-message` on threads with quotes or declines

**Output excerpt:**

| ESS | Vendor | Status | Detail |
|-----|--------|--------|--------|
| 7650 | Oly Signs | Quoted | $2,480 + permits cost + $475 procurement |
| 7661 | Ally Signs | Declined | Manufacturer only |
| 7696 | Sign Safari | Engaged | July timing agreed; no written quote yet |
| 7657 | JNL Sanchez | No response | Sent Jun 8 |
| 7661 | candssigns | No response | Sent Jun 8; verify ESS vs 7662 |

**Summary:** 5 sent, 1 quoted, 1 declined, 1 engaged, 2 no response, ~55 sites remaining.

## Example: forward recommendation

**Quoted thread:** Guy Dragisic, ESS 7650, $2,480

**Draft to Stacie (user approves before send):**

```
Stacie — Guy at Oly Signs quoted ESS 7650 Arlington Heights at $2,480 for
Phase 1 (remove/dispose ESS letters + office sign, install building + pole
banners). Permits at cost + $475 procurement. Assumes regular hours,
unobstructed access, grommets, mechanical fasteners, off-site disposal.
Forward the full thread?
```
