# Vixxo Routing Maps

Use these maps only when the active profile points at a Vixxo workspace and the
target team/project is not already fixed by the profile or the user. Pick the
strongest content match; default to **IT Business Requests** when unclear. The
user confirms or overrides all routing at draft time.

These IDs reflect the Linear workspace as of 2026. If teams or projects change,
refresh this file by querying the Linear MCP `list_teams` / `list_projects`
tools.

## Intake / Promotion Model (business requests)

The IT Business Requests project is an **intake queue**, not the permanent home.

1. **Intake:** a request lands in IT Business Requests with the `Business Request`
   label auto-applied.
2. **Triage:** a reviewer sets priority and picks the owning team/project.
3. **Promotion:** the reviewer changes the project to the target team project.
   The `Business Request` label **stays** — it is the cross-project thread that
   keeps the item visible on Bridge's Business Requests view. It must never be
   removed.
4. **Execution:** the team works the issue in their project; it stays visible on
   Bridge because of the label.

Engineering stories created during decomposition (Side 2) do **not** get the
`Business Request` label — they are implementation work, not business requests.

## Team Routing Map

| Keywords / Signals | Team | Team ID |
|---|---|---|
| VixxoLink, mobile app, Angular, MAUI, spin-up, customer onboarding portal | VixxoLink | `1e933b01-141a-4b69-9574-4ae4f54f2c51` |
| Siebel, CRM, service request, SR, SalesLogix, SLX | Siebel | `e32b7a39-7851-4646-906a-418831c48598` |
| report, Power BI, BO, Business Objects, EDW, dashboard, data warehouse, ViSta, SHWA | Reporting | `5818e76d-161b-417b-928f-bfdce6023754` |
| Gateway, portal, customer portal, web portal | Gateway | `053f4563-c837-46f0-9248-1a5f37edc0af` |
| parts, part request, pricing, product, machine, ChatFPT, VixxoVerify | VixxoVerify | `7919cff9-b806-4b83-a5c8-989304419199` |
| AI, automation, MCP, Claude, N8N, n8n, invoicing automation, cash apps | AI / Automations | `7bd4fe81-d164-4e9e-bd36-94fdf07dae5d` |
| ORMB, JDE, billing, Oracle, revenue management | ORMB 2.0 | `789f67a7-f138-4a62-8f04-4c1a2ee18efc` |
| database, DBA, Oracle DB, SQL, query performance, schema | DBA Ops | `28ede684-7b88-4dac-a1eb-cdac504e93ca` |
| AWS Connect, call center, IVR, phone system, contact center | AWS Connect | `0f7ae054-ba69-461c-9c81-6aa5d8355afe` |
| Dynamics, ERP, invoicing (non-AI), PO, purchase order | Dynamics | `0535af1b-6dea-41c9-9167-b53158e1c8f0` |
| IT ops, endpoint, network, VPN, laptop, hardware, Forcepoint, security | IT OPs | `a2547bf2-64cb-4979-8264-429fd689c2fe` |
| Bridge product, Bridge app, bridge.vixxo.com, Bridge repo, backlog viewer, Bridge admin | Bridge | `ef53a775-61d8-432e-a6dd-bb31d07baa73` |
| general business request, unclear domain, cross-functional | IT Business Requests | `0aeadd2c-b74d-43a7-a7a2-a6918cb39344` |
| general/catch-all for Vixxo-wide items not owned by Bridge or another named team | Vixxo | `e88d881b-d99e-4b62-b8f6-db1a3a900a30` |

## Project Routing Map

| Keywords / Signals | Project | Project ID |
|---|---|---|
| part request, new part, add part | Part Requests | `2d671710-ad5f-4e80-9d00-98225b109946` |
| part request automation, auto-load, skill | Part Request Automations | `89612032-5f96-40ba-a626-1de1dbbcb241` |
| part pricing, price update, cost change | Part Pricing Updates | `26834a41-9a9c-4f1e-a5c9-f40e81ed5c92` |
| machine cleanup, product cleanup | Machine Product Cleanup | `82b11338-c46b-42d8-be64-8e8d4703cfc2` |
| ChatFPT | ChatFPT Management | `424eb0bd-e86e-4e03-9134-afe2b8ee3bc3` |
| Freshwork, support ticket, helpdesk | Freshwork Support Tickets | `77c4dcaf-14ff-41e5-83c3-439a4c8d9e43` |
| MCP, integration, connector | MCPs | `fd419c9c-14e7-4b06-9d52-4262eeb74abf` |
| AI invoicing, invoice AI, smart invoice | AI Invoicing | `52eff846-e0fa-4a45-abed-1f995141870f` |
| ORMB pricing, pricing automation | ORMB Pricing Automation | `ad1a2b7f-b29e-4582-8a81-8f774d04f3bc` |
| ORMB endgame, ORMB migration, ORMB 2.0 | ORMB Endgame | `56210339-8baf-46bb-b846-50ea8b558844` |
| cash apps, cash application | Cash Apps Automation | `29388839-7b82-4ad9-a13c-866ddced207c` |
| N8N, workflow automation | N8N | `4351f610-0ccb-468c-adea-baf35ad2becc` |
| Smartsheet, construction | Construction Smartsheet Automation | `a5a138e3-dd5c-4bce-8f68-0dc12cc2c06f` |
| AI assistant, personal assistant, BMAD | AI Assistant Platform | `3bdc5ffc-3b5b-47b2-af33-1eb0a63a09a6` |
| PolyAI, voice AI, phone AI | PolyAI | `b9f464ef-b5c8-4f8c-9d19-de9cd6165af8` |
| Bridge, bridge project | Bridge | `018f8064-950f-4bc7-864e-0514085bfe2c` |
| SalesLogix migration, SLX to Enterprise | SalesLogix (SLX) to Enterprise Vixxo | `c7d81270-807d-4db5-a19d-93bc53787c6a` |
| support gap, coverage gap, support issue | Support Gaps | `fc1f55d4-a4c9-402d-94ba-11774d7a929d` |
| VixxoLink test, test automation, Playwright, Jest | VixxoLink Web - Test Automation | `89c62c7f-c086-43b0-a3d8-1943b4ea6544` |
| Angular upgrade, framework upgrade | Future-Proofing Our Applications | `970f9ecc-6b6e-4697-b9b0-0fedff6d54b8` |
| ADO migration, Linear migration | ADO to Linear Migration | `df0f99dd-53fd-4743-a223-86c4ce7059ed` |
| general business request, report request | Business Requests | `07d8cc35-0088-4a18-9226-1ae7cff8681e` |
| invoice entry, shared mailbox, Dynamics PO | Invoice Entry Workflow | `afe8c187-28df-4c27-8507-bb3c383766f1` |
| customer credit, credit monitoring | Customer Credit Monitoring | `8eab0908-931a-4475-bc8b-909d5ffa4cab` |
| VixxoLink general, VL dev, spin-up | FY2026 - VixxoLink | `8f43b2af-3721-4e93-a502-73c44b48446d` |
| reporting general, EDW, FY2026 reporting | FY2026 - EDW/Reporting | `3409d7d7-41f0-4b74-8c75-a214c33fe37e` |
| Gateway general | Gateway | `75e4f834-afc6-4475-8fba-57eaa05b1434` |
| transactional business | Transactional Business | `4febddf5-254b-432b-94b0-ce843b3a3d43` |
| SHWA reporting, monthly SHWA | Monthly SHWA Reporting Updates | `16837d90-d87a-4c99-a68b-64d30755af1d` |
| ViSta, Starbucks reporting | ViSta Changes (Starbucks Reporting) | `027af183-314e-4af4-a6b8-3dc639bd6935` |
| historical SLX, SLX data, embedded reports | Historical SLX data | `7473d35e-92ae-421b-b952-faf3f4162619` |
| report request, new report, Business Objects, PowerBI new | VK - New Report Request | `ed60c5a3-f1cc-43fc-a4a8-a8ec9b6bc5fb` |

If no project match is found, omit the project field.

## Category / Routing Label Map

These are separate from Work Type (`Epic`/`Story`/`Chore`/`Bug`) and from the
`Business Owner` label. Apply 1-2 as relevant.

| Signal | Label | Label ID |
|---|---|---|
| Item in Business Requests project, or decomposition Side 1 | Business Request | `94eb9b6f-40f8-4173-8e76-60ec8ea1464f` |
| New feature, add capability, build | Feature | `19196f6b-30be-4d73-aa2a-85428cf8d297` |
| Improve, enhance, optimize | Improvement | `699e7bdf-5c77-4483-bb22-a9ea7f34c612` |
| AI, Claude, automation, MCP related | AI | `f7cfa32e-b1b7-43cb-b932-d7d65eed4bcf` |
| Customer-facing, customer impact | Customer | `ff151011-298e-46f5-be17-6df828b9e2de` |
| Infrastructure, server, deployment, DevOps | Infrastructure | `580fafa1-05a0-43b4-b26e-929c3a749992` |
| Blocked by dependency or external factor | Blocked | `41bc0033-1f3b-4aff-8397-338fb5c5e9fe` |

**Business Request label rule:** always apply `Business Request` to items in the
Business Requests project (intake, decomposition Side 1, or any mode). It is
permanent — never remove it when promoting/moving an issue to a team project.

## Reference IDs

- Bobby (assignee): `6d8b21ed-8298-46e8-ba59-c4916d7b9b68`
- Bridge (project): `018f8064-950f-4bc7-864e-0514085bfe2c`
- Bridge (team): `ef53a775-61d8-432e-a6dd-bb31d07baa73` (key: `BRG`)
- IT Business Requests (team): `0aeadd2c-b74d-43a7-a7a2-a6918cb39344`
- Business Requests (project): `07d8cc35-0088-4a18-9226-1ae7cff8681e`
