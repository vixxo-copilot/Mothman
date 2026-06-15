# BOYD VKS Landlord / Tenant Procedures

## Source Documents

- `~/Downloads/BOYD-VKS Seibel-Landlord Dispatch SOP - 7.21.2025.docx`
- `~/Downloads/VKS Lease Review Common Landlord vs. Tenant Repairs - Kansas- BOYD.docx`
- `~/Downloads/VKS Lease Review Trigger Guide for Out-of-Scope or Landlord-Responsibility Work- BOYD.docx`
- `~/Downloads/Landlord-Tenant Responsibility Report.XLSX`

## SOP Summary

- New BOYD service requests outside equipment requests route to `BYD_LLDREV` for landlord review.
- VKS Kansas Boyd Regional Leads review CoStar, shared CoStar lease abstracts, Siebel site records, and the monthly responsibility report to confirm landlord vs Boyd responsibility.
- If Boyd is responsible, change service contractor from `BYD_LLDREV` to `BYD_TL01`; this routes to the assigned Vixxo team lead by line of service.
- Non-P1 pass-through work for HVAC, Fire Life Safety, Roofing, or Parking Lot/Paving can be directly dispatched by VKS Regional Leads to the pass-through provider when not landlord-responsible.
- If a line of service would never be landlord responsibility for a site, request SPM coverage cleanup so `BYD_LLDREV` is removed from Rank 1 and replaced with `BYD_TL01`.
- If landlord is responsible, reassign to `BYD_LLD`, set spend category to `Landlord`, obtain landlord contact information, and email the landlord with Boyd regional contact copied.
- All landlord repair emails should be sent to `BoydLLRequests@vixxo.com`; include `myfsn@vixxo.com` in CC so the communication appears on the work order.
- Non-emergency landlord requests get three follow-ups within 30 days. If no response after three follow-ups, add dispatched SR/WO marker until Boyd confirms completion.
- Landlord dispatch tickets are billed at `$150.00` per request. Use `No Invoice Pending` / invoice-only VIID process per the SOP.

## Pass-Through Providers

Only these trades bypass Boyd Team Lead Rank 1 coverage when appropriate:

- HVAC: Lennox `KS68581`
- Roofing: Let's Roof `KS68591`
- Fire Life Safety: Academy `KS68696`
- Paving: Let's Pave LLC `KS68595`

## Lease Review Triggers

Return to lease review when scope involves:

- Exterior signage installation, removal, or replacement
- Shared/common areas such as lobbies, hallways, shared walls, loading docks, driveways, landscaping, or irrigation
- New electrical runs, rewiring, or panel upgrades outside tenant walls or tied into shared systems
- HVAC coil, compressor, rooftop unit, or full-unit replacement
- Exterior / below-grade plumbing, main lines, shared restrooms, or pipes outside tenant walls
- Structural items such as roofing, exterior walls, foundation, or cutting into walls
- Exterior painting, especially common or full-building surfaces
- Parking lots, sidewalks, repaving, striping, potholes, or drainage

## Common Responsibility Norms

These are fallback norms only. The workbook and lease abstract control when available.

Common landlord responsibilities:

- Structural elements: roof, foundation, exterior walls
- HVAC systems unless tenant responsibility is specified
- Underground utilities to the building
- Parking lot and common areas
- Capital replacements
- Code compliance issues existing at lease start

Common tenant responsibilities:

- Interior fixtures and finishes
- Plumbing and electrical inside the premises
- Regular maintenance and janitorial
- Signage and window cleaning
- Damage caused by tenant or invitees
- Snow and landscaping in NNN or absolute net leases

HVAC guidance:

- Maintenance usually tenant
- Repairs vary; major or capital repairs may be landlord
- Replacement usually landlord unless absolute-net language pushes it to tenant

## Output Standard

Every check should return:

- SR number if known
- site number and address
- repair item matched from the workbook
- responsible party and reimbursable by values
- recommendation: tenant responsible, landlord responsible, lease review required, or pass-through direct dispatch
- confidence and rationale
- tenant-side lease expert assessment
- lease citation: specific section/page language from the workbook `Repairs - Comments`
- next operational action
