# Freshdesk Internal Note — COI Review Findings (Mode B)

Use this skeleton when posting `conversations_manage create_note` (private = true) on a COI ticket. The internal note is the **durable audit record** of what was checked and what was found — post it BEFORE the public SP-facing reply so the record exists even if the reply send fails.

This note is internal-only. It is not visible to the service provider. Be precise; cite the values from the COI.

---

**COI Review — {Service Provider Name}**
Reviewer: HABLADORA AI assistant for Maria (drafted; sent under operator approval)
COI effective date: {COI Effective Date}
Insurer(s): {Insurer Names}
Policy numbers: {GL Policy #}, {Auto Policy #}, {WC Policy #}, {Umbrella Policy # if any}

**Compliance summary:** {one of: "MEETS Vixxo's minimum requirements" / "DOES NOT meet Vixxo's minimum requirements — corrections requested" / "BLOCKED — COI missing or illegible, cannot review"}

## Findings (per Vixxo checklist — `references/vixxo-requirements.md`)

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Insured name matches SP legal name | {Compliant / Missing / Deficient / Needs clarification} | {value or note} |
| 2 | Policy dates current (not expired; not within 30 days) | {…} | Earliest expiry: {date} |
| 3 | CGL — occurrence form, all six limit fields populated | {…} | Each Occ: {$}, Gen Agg: {$}, Prod/Comp Op Agg: {$}, Pers/Adv Inj: {$}, Damage Rented: {$}, Med Exp: {$} |
| 4 | CGL — aggregate-applies-per box selected | {…} | {Policy / Project / Loc} |
| 5 | Auto Liability — limit(s) populated and scope box checked | {…} | CSL: {$} or BI/PD: {$/$/$}; scope: {Any / Owned+Hired+Non-Owned / …} |
| 6 | Umbrella/Excess present if needed to reach contracted totals | {…} | Each Occ: {$}, Agg: {$} or N/A |
| 7 | WC — statutory box indicated | {…} | |
| 8 | EL — Each Accident populated | {…} | {$} |
| 9 | EL — Disease Each Employee populated | {…} | {$} |
| 10 | EL — Disease Policy Limit populated | {…} | {$} |
| 11 | Proprietor/Partner exclusion question answered (and explained if Yes) | {…} | {Yes/No + explanation} |
| 12 | Additional Insured — full Vixxo wording present (verbatim or materially equivalent) | {…} | {quote what was actually present} |
| 13 | Endorsement CG 20 10 04/13 (or equivalent) referenced | {…} | {form number/edition seen, or "not referenced"} |
| 14 | Endorsement CG 20 37 04/13 (or equivalent) referenced | {…} | {form number/edition seen, or "not referenced"} |
| 15 | Endorsement CA 20 48 10/13 (or equivalent) referenced | {…} | {form number/edition seen, or "not referenced"} |
| 16 | Primary and non-contributory wording present for GL | {…} | |
| 17 | Waiver of Subrogation — GL | {…} | |
| 18 | Waiver of Subrogation — Auto | {…} | |
| 19 | Waiver of Subrogation — WC / EL | {…} | |
| 20 | 30 days' Notice of Cancellation referenced | {…} | |
| 21 | Certificate Holder — exact name, street, suite, city, state, ZIP | {…} | {what was on the COI vs required; remember: Dobson Rd address required for COIs dated **3/16/2026 or later**, E Shea Blvd. is acceptable for earlier dates — see SKILL.md "Vixxo's minimum requirements" section} |

## Outcome

- **Ticket `type` set to:** {COIs (unchanged) / **Account Update** (compliant outcome only)}
- **Custom fields set:** {**`cf_sp: "<SP company name>"`** (REQUIRED on any status:4 update — both COIs and Account Update — see SKILL.md "Required field on resolution" note) / **`cf_vixxo_link_type_of_request: "Profile Update"`** (compliant outcome only)}
- **Tags applied:** {COI, risk-compliance-routed, coi-reviewed, [coi-deficient | coi-compliant + coi-accepted | coi-clarification-pending | coi-blocked], …}  *(tags ≤ 32 chars each; Freshdesk replaces the array on update — include existing tags)*
- **Status set:** {Pending (3) — clarification/blocked / **Resolved (4)** — deficient (auto-reopens on SP reply) or compliant / Closed (5) — compliant + operator confirmed final}
- **Update path used:** {MCP `tickets_manage update` (Pending only) / **REST API bypass `PUT /api/v2/tickets/{id}`** (mandatory for status:4 — MCP rejects status:4 with generic Validation failed; see SKILL.md step 7.4)}
- **Public reply posted:** {Yes — see next entry in conversation / Forward to broker (internal-forward COI — see SKILL.md "Internal-forward COI handling") / No — see reason}
- **Siebel handoff note posted (compliant only):** {Yes — see follow-on internal note / N/A — non-compliant outcome}
- **Operator approval:** {operator name / "approved on {timestamp}"}

## Notes / exceptions

{free text — anything the next reviewer should know if the SP resubmits, e.g., "SP requested partial waiver of CG 20 37 — escalated to {name}", or "COI was an attachment in the second message of the thread, not the first"}
