# Company Vetting — KS Onboarding routing

Run Gateway + VixxoLink + Salesforce search before setting `cf_sp` or posting
the routing note.

Full search order, fuzzy matching, and scoring rules live in
[../../sp-inbound-vetting/reference/company-vetting.md](../../sp-inbound-vetting/reference/company-vetting.md).
This file adds **routing-specific cf_sp rules only**.

## Vetting output table (required in every packet)

| System | Entity | Match | Identifier | Status / notes |
| --- | --- | --- | --- | --- |
| Gateway / Siebel | Service Provider | Yes / No / Possible | SP # + display name | Source tool + match key |
| VixxoLink | Service Provider | Yes / No / Possible | SP # + name from SR | When SR resolved |
| Salesforce | Lead | Yes / No / Possible | Lead Id | Status, LastModifiedDate |
| Salesforce | Case | Yes / No / Possible | Case Id | Status, Subject |

**Overall posture:** `Known SP` | `Possible SP (Gateway)` |
`Prospect (SF Lead)` | `Open SF Case` | `Unknown / Not in systems`

## cf_sp decision (routing skill)

| Posture | Confidence | `cf_sp` on type change |
| --- | --- | --- |
| Known SP (exact email, KS/SR, or normalized company equality) | High | Set `{SP_NUMBER} - {Gateway display name}` |
| Possible SP (fuzzy ≥ 0.75) | High | Set if single clear winner; else **blank** |
| Possible SP | Medium / Low | **Blank** |
| Prospect (SF Lead only) | Any | **Blank** — do not use Lead company as cf_sp |
| Unknown | Any | **Blank** |

**Do not** set `cf_sp` to `Unknown`, a guessed company name, or Lead `Company`
when posture is not Known SP with High confidence.

**Do not overwrite** existing `cf_sp` populated by an operator — note conflict
in the internal note instead.

## Search shortcuts

Reuse [../../sp-inbound-vetting/scripts/entity_match.py](../../sp-inbound-vetting/scripts/entity_match.py)
normalization and scoring when running batch scripts.

Identification priority: requester **email** → **contact name** → KS/SR # →
company string (with Gateway tracking-prefix strip).
