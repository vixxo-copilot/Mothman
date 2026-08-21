# Freshdesk ↔ Salesforce Duplicate Scan (COI widened)

**Window:** 2026-06-26T00:00:00+00:00 → 2026-07-01T17:06:46.462537+00:00

## Summary

| Metric | Count |
|--------|------:|
| FD inbound | 794 |
| SF Cases | 253 |
| Duplicate pairs | 31 |
| True same-thread | 4 |
| Likely same-thread | 1 |
| Contact collision | 26 |
| COI Req-id matched | 0 |
| COI provider-matched | 0 |

## Intra-system Req-id duplicates (route, do not re-create)

### Salesforce — same Req id, multiple Cases

**150-339-0 Req 201** (CECCO, Inc.)
- 00006053 — Working — Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 201~2026-06-29 23
- 00006107 — Closed — RE: Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 201~2026-06-2

**365-728-5 Req 365** (Smelscer Plumbing, Inc.)
- 00005986 — New — Fwd: FW: Certificate Of Insurance - Smelscer Plumbing, Inc. 365-728-5 
- 00006007 — New — Fw: Certificate Of Insurance - Smelscer Plumbing, Inc. 365-728-5 Req 3

## Federated sender collisions (no provider match)

| FD | FD provider | SF Case | SF subject |
|----|-------------|---------|------------|
| #60160 | Tri Star Transport LLC | 00005915 | Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 200~202 |
| #60160 | Tri Star Transport LLC | 00006015 | Certificate Of Insurance - Superior Mechanical Services, Inc |
| #60160 | Tri Star Transport LLC | 00006016 | Certificate Of Insurance - Angeles Plumbing, LLC 450-802-4 R |
| #60160 | Tri Star Transport LLC | 00006048 | Certificate Of Insurance - KAA Investments LLC 329-159-8 Req |
| #60160 | Tri Star Transport LLC | 00006053 | Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 201~202 |
| #60160 | Tri Star Transport LLC | 00006077 | Certificate Of Insurance - Storefronts and Entrances, Inc. 1 |
| #60160 | Tri Star Transport LLC | 00006127 | Certificate Of Insurance - Bergstrom Electric Inc 215-989-5  |
| #60160 | Tri Star Transport LLC | 00006131 | Certificate Of Insurance - Pannell Builders, LLC 440-947-0 R |
| #60160 | Tri Star Transport LLC | 00006136 | Certificate Of Insurance - Water Treatment Technologies, Inc |
