# Salesforce Case Review — Created ≥ 2026-06-26

**Generated:** 2026-07-01 17:12 UTC
**Source:** live SOQL (`CreatedDate >= 2026-06-26T00:00:00Z`)

## Summary

| Metric | Count |
|--------|------:|
| Total Cases | 253 |
| Open (actionable) | 212 |
| Federated COI (Req id parsed) | 17 |
| COI duplicate Req groups | 2 |
| Excess COI Cases (merge candidates) | 2 |
| Open on Shell Account | 112 |
| FD cross-ref in Description | 4 |

### By RecordType

| RecordType | Count | Open |
|------------|------:|-----:|
| Service Provider Support | 231 | 195 |
| Recruitment Request | 11 | 10 |
| Provider Onboarding | 4 | 1 |
| Rate Negotiation | 4 | 4 |
| Coverage Change | 3 | 2 |

### By Status

| Status | Count |
|--------|------:|
| New | 203 |
| Closed | 36 |
| Working | 7 |
| Agreement Signed | 2 |
| Pending Finance Approval | 1 |
| Not Filled | 1 |
| Enablement | 1 |
| On Hold | 1 |
| Compliance In Progress | 1 |

## Federated COI — intra-SF duplicates (same policy + Req id)

Consolidate to **primary**; close/archive others.

| Provider | Req key | Cases | Open | Primary | Merge/close |
|----------|---------|------:|-----:|---------|-------------|
| CECCO, Inc. | `150-339-0 Req 201` | 2 | 1 | **00006053** (Working) | 00006107 |
| Smelscer Plumbing, Inc. | `365-728-5 Req 365` | 2 | 2 | **00005986** (New) | 00006007 |

### CECCO, Inc. — Req 201

| Case | Status | Account | Owner | Created | Subject |
|------|--------|---------|-------|---------|---------|
| 00006053 (primary) | Working | KS - Bluefield Glass & Interiors | Andrea Heppler | 2026-06-30 | Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 201~2026-06-29 23:19:10.0~0 |
| 00006107 | Closed | KS - Bluefield Glass & Interiors | Andrea Heppler | 2026-06-30 | RE: Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 201~2026-06-29 23:19:10 |

### Smelscer Plumbing, Inc. — Req 365

| Case | Status | Account | Owner | Created | Subject |
|------|--------|---------|-------|---------|---------|
| 00005986 (primary, shell ⚠) | New | Service Provider Support Shell Account | Andrea Heppler | 2026-06-29 | Fwd: FW: Certificate Of Insurance - Smelscer Plumbing, Inc. 365-728-5 Req 365~20 |
| 00006007 (shell ⚠) | New | Service Provider Support Shell Account | Crystal Gagner | 2026-06-29 | Fw: Certificate Of Insurance - Smelscer Plumbing, Inc. 365-728-5 Req 365~2026-02 |

## Open Cases on Shell Account (fix Account)

| Case | Status | Owner | Created | Subject |
|------|--------|-------|---------|---------|
| 00005906 | New | Andrea Heppler | 2026-06-26 | RE: GL and WC COI from Denair HVAC |
| 00005907 | New | Crystal Gagner | 2026-06-26 | Proof of Insurance for Peak Season, Inc. |
| 00005915 | New | Crystal Gagner | 2026-06-26 | Certificate Of Insurance - CECCO, Inc. 150-339-0 Req 200~2026-06-26 09 |
| 00005920 | New | Shelby Hansard | 2026-06-26 | RE: new vendor |
| 00005922 | New | Andrea Heppler | 2026-06-26 | Re: Re: Profi Facilities Maintenance LLC - Ks - Insurance |
| 00005923 | New | Adrienne Adams | 2026-06-26 | Re: Vixxo Kansas Invoice Pay outs |
| 00005926 | New | Andrea Heppler | 2026-06-26 | RE: Plaza Retail, Andy's Ace Hardware COI |
| 00005928 | New | Shelby Hansard | 2026-06-26 | Re: DesignTeam Inc - Service Provider number KS102207 - Your account V |
| 00005930 | New | Shelby Hansard | 2026-06-26 | RE: Onboarding with Vixxo |
| 00005933 | New | Andrea Heppler | 2026-06-26 | Plaza Retail, Andy's ACE |
| 00005934 | New | Crystal Gagner | 2026-06-26 | ASAP Sands Outdoor Services Inc. - Renewal COI |
| 00005937 | New | Adrienne Adams | 2026-06-26 | SR#: 1-6579093301 | WO# | Stryker (Howmedica)-Cushman & Wakefield - Ha |
| 00005940 | New | Andrea Heppler | 2026-06-26 | [Request received] Fwd: Glassma LLC has updated their business insuran |
| 00005942 | New | Crystal Gagner | 2026-06-26 | [Request received] Fwd: Glassma LLC has updated their business insuran |
| 00005945 | New | SP Support | 2026-06-26 | Re: No ETA has been entered - Academy Sports - Wilmington/NC - 0290 |
| 00005955 | New | Crystal Gagner | 2026-06-26 | Proof of Insurance for Legacy Electric, LLC |
| 00005956 | New | Andrea Heppler | 2026-06-26 | One Call Retail Services Inc. Certificate |
| 00005957 | New | Crystal Gagner | 2026-06-26 | Certificate - Vixxo Kansas, LLC |
| 00005959 | New | SP Support | 2026-06-26 | RE: RE: SR#: 1-6575922302 | WO# 352266755 | Ulta Beauty - Pearl City/H |
| 00005960 | New | Crystal Gagner | 2026-06-26 | 2026-27 Renewal Certificate | Christenson Electric, Inc. |
| 00005962 | New | Andrea Heppler | 2026-06-27 | Certificate(s) of Insurance from Aon |
| 00005970 | New | Christopher Ferri | 2026-06-28 | Re: Rate change KS68874 |
| 00005977 | New | Andrea Heppler | 2026-06-29 | Proof of Insurance for Palmetto Topco L.P. and Subsidiaries Commercial |
| 00005979 | New | Crystal Gagner | 2026-06-29 | Proof of Insurance for Palmetto Topco L.P. and Subsidiaries Commercial |
| 00005980 | New | Andrea Heppler | 2026-06-29 |  |
| 00005981 | New | Andrea Heppler | 2026-06-29 | Proof of Insurance for All Coffee Concepts Sales & Service LLC |
| 00005983 | New | Crystal Gagner | 2026-06-29 | Fwd: FW: Certificate Of Insurance - Superior Mechanical Services, Inc. |
| 00005986 | New | Andrea Heppler | 2026-06-29 | Fwd: FW: Certificate Of Insurance - Smelscer Plumbing, Inc. 365-728-5  |
| 00005987 | New | Crystal Gagner | 2026-06-29 | C & L Locksmith COI with all endorsements Attn: Andrea Heppler |
| 00005990 | New | Andrea Heppler | 2026-06-29 | RE: KINNEENG-COI |
| 00005991 | Working | Sheyanne Torallo | 2026-06-29 | Re: Issues with Vixxo Link |
| 00005994 | New | Crystal Gagner | 2026-06-29 | Fwd: Message from 2nd floor - Federated Insurance Auto Reply: Your req |
| 00005997 | New | Crystal Gagner | 2026-06-29 | Re: Action Required: Vixxo Corporation SP Insurance Update |
| 00005998 | New | Crystal Gagner | 2026-06-29 | Updated COI |
| 00006003 | New | Andrea Heppler | 2026-06-29 | Fwd: Message from 2nd floor - Federated Insurance Auto Reply: Your req |
| 00006005 | New | Andrea Heppler | 2026-06-29 | Re: FW: COI |
| 00006007 | New | Crystal Gagner | 2026-06-29 | Fw: Certificate Of Insurance - Smelscer Plumbing, Inc. 365-728-5 Req 3 |
| 00006008 | New | Andrea Heppler | 2026-06-29 | Renewal Certificate of Insurance for J-Hawk Plumbing |
| 00006010 | New | Crystal Gagner | 2026-06-29 | Fwd: Message from 2nd floor - Federated Insurance Auto Reply: Your req |
| 00006011 | New | Shelby Hansard | 2026-06-29 | Re: MI-HVAC- Vendor onboarding- Detroit’s Finest Mechanical Contractor |
| 00006013 | New | Adrienne Adams | 2026-06-29 | Vixxo Link - No Data Found |
| 00006015 | New | Crystal Gagner | 2026-06-29 | Certificate Of Insurance - Superior Mechanical Services, Inc. 392-690- |
| 00006018 | New | Crystal Gagner | 2026-06-29 | SECURITY CENTRAL, INC. Certificate Requested |
| 00006020 | New | Crystal Gagner | 2026-06-29 | Corrected Renewal COI for J-Hawk Plumbing |
| 00006021 | New | SP Support | 2026-06-29 | HSLS Houston LLC invoice is past due |
| 00006023 | New | Crystal Gagner | 2026-06-29 | RE: Message from 2nd floor |
| 00006024 | New | Andrea Heppler | 2026-06-29 | Certificate of Insurance Requested for APi Group Life Safety USA LLC D |
| 00006025 | New | Crystal Gagner | 2026-06-29 | Certificate of Insurance Requested for APi Group Life Safety USA LLC D |
| 00006028 | New | SP Support | 2026-06-29 | Re: SR 1-6576030752 4718 - Sam's Club Cafe - South Jordan |
| 00006030 | New | Crystal Gagner | 2026-06-29 | RE: Certificate of Insurance Requested for APi Group Life Safety USA L |
| 00006032 | New | SP Support | 2026-06-29 | DOGGIE DISTRICT.................WO#6589468372................INVOICE#5 |
| 00006033 | New | SP Support | 2026-06-29 | DOGGIE DISTRIST...............WO#6582064512..............INVOICE#58052 |
| 00006034 | New | SP Support | 2026-06-29 | Estimate #8325 from Brown Aerobic Septic Specialists |
| 00006038 | New | Crystal Gagner | 2026-06-29 | FSVZ VIXXO Recorded Transaction Notification – Finance Alert  / Mon, J |
| 00006039 | New | Andrea Heppler | 2026-06-29 | Automatic reply: Emailing: Pride Enterprises auto dec page |
| 00006040 | New | Crystal Gagner | 2026-06-29 | Fwd: Certificate Of Insurance - Bergstrom Electric Inc 215-989-5 Req 2 |
| 00006041 | New | Andrea Heppler | 2026-06-29 | Fwd: Certificate Of Insurance - Water Treatment Technologies, Inc. 397 |
| 00006043 | New | Crystal Gagner | 2026-06-29 | Proof of Insurance for RoofConnect Logistics, Inc. |
| 00006044 | New | Andrea Heppler | 2026-06-29 | Automatic reply: Updated COI, Plaza Retail, Andy's Ace Hardware |
| 00006045 | New | Crystal Gagner | 2026-06-29 | Automatic reply: Fortney Refrigeration Company / 26/27 Eff 7/1/2026 Re |
| 00006046 | New | Andrea Heppler | 2026-06-29 | Fwd: Certificate Of Insurance - J Noble Binns Plumbing Company Inc 309 |
| 00006047 | New | Crystal Gagner | 2026-06-29 | RE: Message from 2nd floor |
| 00006049 | New | Crystal Gagner | 2026-06-29 | Re: COI KNS Construction, inc |
| 00006050 | New | Andrea Heppler | 2026-06-29 | Certificate of Insurance for Preferred Electric, LLC |
| 00006051 | New | Andrea Heppler | 2026-06-29 | [Next Insurance] Re: [Action Required] Request for a Certificates of I |
| 00006058 | New | Crystal Gagner | 2026-06-30 | Proof of Insurance for Mark One Electric Co., Inc. |
| 00006060 | New | Adrienne Adams | 2026-06-30 | Subcontractor agreement. Summit HVAC- First Service Networks, Inc (Vix |
| 00006065 | New | SP Support | 2026-06-30 | RE: RE: Stryker - Houston |
| 00006066 | New | SP Support | 2026-06-30 | SR Number: 1-6590217722 for Coverage Review |
| 00006068 | New | SP Support | 2026-06-30 | Vixxo.Com |
| 00006070 | New | SP Support | 2026-06-30 | RE: SR#: 1-6577056245 | WO# 351902724 | Columbia Sportswear Co. - Canu |
| 00006071 | New | Crystal Gagner | 2026-06-30 | Proof of Insurance for DMR Mechanical, LLC |
| 00006078 | New | Crystal Gagner | 2026-06-30 | RE: FW: Proof of Insurance for Mark One Electric Co., Inc. |
| 00006080 | New | SP Support | 2026-06-30 | 1-6594900882 |
| 00006081 | New | Adrienne Adams | 2026-06-30 | Re: Issues with Vixxo Link |
| 00006082 | New | SP Support | 2026-06-30 | Reminder: Invoice 6287478 is due from Spears Services, Inc. - $864.61 |
| 00006083 | New | SP Support | 2026-06-30 | Reminder: Invoice 6287512 is due from Spears Services, Inc. - $341.25 |
| 00006084 | New | SP Support | 2026-06-30 | Reminder: Invoice 6287478 is due from Spears Services, Inc. - $864.61 |
| 00006085 | New | SP Support | 2026-06-30 | Reminder: Invoice 6287512 is due from Spears Services, Inc. - $341.25 |
| 00006086 | New | Andrea Heppler | 2026-06-30 | Certificate of Insurance - Hubbs Heating & Cooling |
| 00006088 | New | Crystal Gagner | 2026-06-30 | Proof of Insurance for Fire Safety Systems, Inc. |
| 00006090 | New | SP Support | 2026-06-30 | Re: SR 1-6576030752 4718 - Sam's Club Cafe - South Jordan |
| 00006092 | New | SP Support | 2026-06-30 | Statement from: Overhead Door of Boise |
| 00006094 | New | SP Support | 2026-06-30 | New payment request from A Mobile Locksmith - invoice 108986 |
| 00006096 | New | SP Support | 2026-06-30 | Past Due  payment request from A Mobile Locksmith - invoice 108894 |
| 00006097 | New | SP Support | 2026-06-30 | New payment request from A Mobile Locksmith - invoice 109610 |
| 00006099 | New | Crystal Gagner | 2026-06-30 | Revised COI for Martin Long DBA Long Home Improvement & Repair |
| 00006100 | New | Adrienne Adams | 2026-06-30 | FW: Address change - Peak Season |
| 00006102 | New | Shelby Hansard | 2026-06-30 | Re: MI-HVAC- Vendor onboarding- Detroit’s Finest Mechanical Contractor |
| 00006109 | New | Crystal Gagner | 2026-06-30 | RE: [EXTERNAL] Fwd: Advanced Mechanical Systems Inc - SP# 2990 |
| 00006110 | New | Shelby Hansard | 2026-06-30 | Stealth Services SoCal |
| 00006112 | New | Andrea Heppler | 2026-06-30 | Certificate of Insurance for Wind River Environmental, LLC |
| 00006115 | New | Crystal Gagner | 2026-07-01 | Renewal - Certificate of Insurance for NV5 Global, Inc. |
| 00006117 | New | Crystal Gagner | 2026-07-01 | New 30 days notice of cancellation approved for Brian Turner Commercia |
| 00006120 | New | SP Support | 2026-07-01 | Automatic reply: Vixxo Monthly Business Summary (-) - June 2026 |
| 00006121 | New | SP Support | 2026-07-01 | Ticket Received - [EXTERNAL]  Vixxo Monthly Business Summary (-) - Ju |
| 00006122 | New | SP Support | 2026-07-01 | Automatic reply: Vixxo Monthly Business Summary –(-) - June 2026 |
| 00006123 | New | Crystal Gagner | 2026-07-01 | Evansville Handyman Insurance Changes 7/1/26 |
| 00006124 | New | SP Support | 2026-07-01 | Ticket Received - [EXTERNAL]  Vixxo Monthly Business Summary (-) - Ju |
| 00006125 | New | SP Support | 2026-07-01 | Ticket Received - [EXTERNAL]  Vixxo Monthly Business Summary (-) - Ju |
| 00006127 | New | Andrea Heppler | 2026-07-01 | Certificate Of Insurance - Bergstrom Electric Inc 215-989-5 Req 2620~2 |
| 00006129 | New | Crystal Gagner | 2026-07-01 | New 30 days notice of cancellation approved for D.A Maintenance LLC |
| 00006130 | New | SP Support | 2026-07-01 | Re: Vixxo Monthly Business Summary (-) - June 2026 |
| 00006131 | New | Crystal Gagner | 2026-07-01 | Certificate Of Insurance - Pannell Builders, LLC 440-947-0 Req 61~2026 |
| 00006134 | New | SP Support | 2026-07-01 | Fwd: Rate Changes |
| 00006136 | New | SP Support | 2026-07-01 | Certificate Of Insurance - Water Treatment Technologies, Inc. 397-439- |
| 00006137 | New | SP Support | 2026-07-01 | Re: *FOLLOW UP* Portal Inquiry from Pop A Lock |
| 00006138 | New | SP Support | 2026-07-01 | Reminder: Invoice 6287489 is due from Spears Services, Inc. - $331.00 |
| 00006139 | New | SP Support | 2026-07-01 | Reminder: Invoice 6287489 is due from Spears Services, Inc. - $331.00 |
| 00006140 | New | SP Support | 2026-07-01 | Re: Vixxo Monthly Business Summary (-) - June 2026 |
| 00006141 | New | SP Support | 2026-07-01 | Vixxo Facility Solutions |
| 00006143 | New | SP Support | 2026-07-01 | Erling Sales & Service LLC - Renewal Cert |

## Freshdesk cross-refs (Description contains Freshdesk #)

| SF Case | FD ticket | Subject |
|---------|-----------|---------|
| 00005919 | #59559 | Fwd: New voicemail from Andrea Spicer via VENDOR RELATIONS |
| 00005932 | #59653 | Fwd: New voicemail from Roberts Plumb via VENDOR RELATIONS |
| 00005946 | #59717 | Fwd: New voicemail from WIRELESS CALLER via VENDOR RELATIONS |
| 00005953 | #59724 | Fwd: New voicemail from ELECTRONIC RECY via VENDOR RELATIONS |

## All open Federated COI Cases (single + duplicate)

| Case | Status | Account | Owner | Req | Provider |
|------|--------|---------|-------|-----|----------|
| 00006040 | New | Service Provider Support Shell Account | Crystal Gagner | Req 2603 | Bergstrom Electric Inc |
| 00006127 | New | Service Provider Support Shell Account | Andrea Heppler | Req 2620 | Bergstrom Electric Inc |
| 00005915 | New | Service Provider Support Shell Account | Crystal Gagner | Req 200 | CECCO, Inc. |
| 00006053 | Working | KS - Bluefield Glass & Interiors | Andrea Heppler | Req 201 | CECCO, Inc. |
| 00006046 | New | Service Provider Support Shell Account | Andrea Heppler | Req 1694 | J Noble Binns Plumbing Company Inc |
| 00006131 | New | Service Provider Support Shell Account | Crystal Gagner | Req 61 | Pannell Builders, LLC |
| 00005986 | New | Service Provider Support Shell Account | Andrea Heppler | Req 365 | Smelscer Plumbing, Inc. |
| 00006007 | New | Service Provider Support Shell Account | Crystal Gagner | Req 365 | Smelscer Plumbing, Inc. |
| 00005983 | New | Service Provider Support Shell Account | Crystal Gagner | Req 217 | Superior Mechanical Services, Inc. |
| 00006015 | New | Service Provider Support Shell Account | Crystal Gagner | Req 222 | Superior Mechanical Services, Inc. |
| 00006041 | New | Service Provider Support Shell Account | Andrea Heppler | Req 1 | Water Treatment Technologies, Inc. |
| 00006136 | New | Service Provider Support Shell Account | SP Support | Req 12 | Water Treatment Technologies, Inc. |