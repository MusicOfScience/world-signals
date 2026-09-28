# Step 12A — RBNZ Relationship candidate

Status: `READY_FOR_HUMAN_RELATIONSHIP_REVIEW`

This retained audit candidate extends the Relationship contract to v0.2 and
pins two already-admitted World State component revisions:

- source: `WSDIM-MACRO-NZ-RBNZ-OCR-202609-001-R1`
- target: `WSDIM-MARKETS-NZ-RBNZ-OCR-202609-001-R1`

The candidate is a directed `ASSOCIATION`, not a causal relationship,
mechanistically supported transmission or forecast. Direction records the
reviewed temporal ordering of policy-path information and the source-reported
market response; it does not prove causality.

The temporal scope uses the RBNZ release at
`2026-09-02T02:00:00Z` as an event anchor, while retaining civil-date and
source-reported-window precision for the market response. Exact onset and end
are unknown and are not fabricated.

Analysis and exact evidence hashes are supporting lineage only. The endpoint
components both currently report `NO_CURRENTNESS_CLAIM`; that does not prevent
a historical candidate and does not make the candidate a current transmission
channel.

The candidate preserves alternative explanations, confounders, falsifiers and
the shared-lineage limitation. It remains `UNDER_REVIEW`, `UNRESOLVED`,
`INTERNAL_ONLY`, has no production write targets, and is excluded from active
graph output. The production Relationship dataset remains empty and closed.

Candidate semantic fingerprint:
`398efdf39448a9676bdd099a38fc3f66ac47a69cac1001b3895f493601679221`

Source-manifest fingerprint:
`a4ecd251fa4f6e57020f0fcf6f0e0427e0cdb8a1d392ed34068d2d73b13fabbe`

Step 12B remains a separate human Relationship review and admission decision.
