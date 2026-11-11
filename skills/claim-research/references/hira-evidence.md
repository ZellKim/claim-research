# HIRA semantic evidence

This is a human-authored static evidence register and is never auto-rewritten or automatically rewritten.

- Last reviewed: 2026-07-22
- Latest incorporated source observation: 2026-07-14 (HI-029)
- Coverage: scoped evidence for the verified 2025Q4 customized/full extract profile and historical patient-sample material; limited for live server state and study-specific definitions.

## Known evidence gaps

- Live `PROC CONTENTS` or equivalent output for the active study extract.
- Study-specific SAP, code lists, data-request period, and actual table suffix.
- Active server package versions and institution-specific execution constraints.
- Current approval for exposure, outcome, covariate, exclusion, denominator, and episode definitions.

## Verified 2025Q4 customized/full extract profile

The prior customized/full provenance and HI-029 apply only to this delivered profile. In it, T200, T300, T400, and T530 were observed with direct `JID` and `MID`; T300 used `DIV_CD`; T530 used `DIV_CD` and `MEFT_DIV_NO`; and T200 was the observed date source. HI-029 supports direct T400 `JID`/`MID` counting only for this profile when the extract is already period-limited and the active layout and grain are revalidated.

## Historical official patient-sample profile

The official local workbook `(첨부7)환자표본자료_변수설명서(2015년 이후).xlsx` is historical patient-sample evidence, not evidence of a current schema. Its sheet observations are coordinates, not universal claims:

- T200: `SPEC_ID_SNO` B2; `FOM_TP_CD` B7; `JID` B16; `PAT_AGE` B22; `RECU_FR_DD` B54.
- T300: `SPEC_ID_SNO`; `DIV_CD` B11; `GNL_NM_CD` B23; no verified `JID` in that sheet.
- T400: `SPEC_ID_SNO`; `SICK_CD` B5; no verified `JID` in that sheet.
- T530: `SPEC_ID_SNO`; `GNL_NM_CD` B11; no verified `JID` in that sheet.

## Evidence register

| Fact | Provenance locator | Last checked | Confidence | Boundary |
| --- | --- | --- | --- | --- |
| Profile-specific keys and fields | Verified 2025Q4 customized/full delivered-layout materials | 2026-06-15 | High for that delivery | Reinspect the active extract; do not transfer the map to NPS or other deliveries. |
| Historical NPS fields and coordinates | `(첨부7)환자표본자료_변수설명서(2015년 이후).xlsx` | 2026-07-22 | High for workbook observation | Historical only; not evidence of a current layout. |
| `FOM_TP_CD` width and `PAT_AGE = 999` handling | HIRA reference and issue evidence | 2026-06-15 | High in observed material | Confirm the active profile and approved handling. |
| Raw table suffixes vary by study | `known-issues.md`; `HIRA_work/HIRA_ISSUES.md` | 2026-06-15 | High | Never promote one observed suffix into a general rule. |
| One-table-one-scan and raw-before-summary safeguards | Common issue database; claims SAS guidance | 2026-06-15 | High | Current project rules govern persistence and resource limits. |
| HIRA R handoff used `haven::read_sas` and `data.table` | HIRA issue evidence; project instructions | 2026-06-15 | Medium | Verify active packages and environment constraints. |
| Direct period-limited T400 counting | HIRA issue HI-029; study feedback | 2026-07-14 | High for the 2025Q4 customized/full profile | Revalidate layout, period, keys, and analysis grain. |
| Domain-specific clinical definitions stay outside this layer | Approved SAP/domain references | 2026-07-14 | High | Require explicit study approval. |

## Source inventory and portability

The provenance locators above describe sources used to synthesize this reference; they are not runtime dependencies. Current project issue sources, a study `RESEARCH_LOG.md`, delivered-layout inventory, or domain reference are newer project evidence when present. No exact machine paths are bundled here.

## Update boundary

Update this file and `hira-semantic-layer.md` only through human review of authoritative, privacy-safe evidence. New reusable observations first follow the `nhis-hira` learning contract. Compatibility fixes may enter renderer-owned learned references only when policy-eligible; table and domain facts require approved provenance, version/date/scope, and explicit approval.

Do not copy raw patient or claim rows, identifiers, small-cell outputs, credentials, server paths, raw logs, or unrestricted command output into either HIRA reference.
