# HIRA semantic layer

Read `guardrails.md` first. This human-authored static reference adds HIRA-specific retrieval detail only after the HIRA route has been selected and is never auto-rewritten or automatically rewritten. Never apply it to an NHIS route. Current project instructions, approved study documents/SAP, the active schema, and current environment evidence outrank every statement here.

## Contents

- Delivery profiles and field maps
- Study and episode preflight
- Filters and code matching
- Reusable query patterns
- QC, compatibility, and R handoff

## Identify the delivery profile first

Inspect the delivered layout with `PROC CONTENTS` or an equivalent inventory before choosing fields or joins. Never mechanically translate names between profiles.

### Verified 2025Q4 customized/full extract profile

These are observations for the verified 2025Q4 customized/full extract profile only:

| Table | Use | Observed keys and fields | Boundary |
| --- | --- | --- | --- |
| T200 | Cohort base and dates | direct `JID` and `MID`; `RECU_FR_DD` | Observed date source; verify type and format in the active delivery. |
| T300 | Procedures and treatment detail | direct `JID` and `MID`; `DIV_CD` | Do not mechanically substitute another medication-field name. |
| T400 | Diagnoses | direct `JID` and `MID`; `SICK_CD` | For an already period-limited extract, direct counting is conditional on this profile. |
| T530 | Outpatient prescription detail | direct `JID` and `MID`; `DIV_CD`, `MEFT_DIV_NO` | Validate whether T300, T530, or both implement the SAP medication definition. |

For this profile, derive dates once from T200 when numeric dates or narrower temporal logic are required. Do not add T200 to an already period-limited T400 count unless the analysis needs dates, narrower periods, follow-up, costs, visit form, or statement-only fields.

### Historical official NPS/patient-sample profile

The historical official patient-sample workbook observes statement identifier `SPEC_ID_SNO`. T300 may lack `JID`; T400 may lack `JID`; and T530 may lack `JID`, so patient-level detail, diagnosis, or prescription linkage may require verified T200 linkage when those sheets omit the patient key. Medication variables can include `GNL_NM_CD`. `PROC CONTENTS` or an equivalent delivered-layout inventory is the final authority; this historical profile is not a current universal schema.

Across verified layouts, treat `FOM_TP_CD` as a 3-character field only when the inventory confirms it. Use only study-validated values such as `021` or `031`; a 1-character filter can return zero rows. Handle `PAT_AGE = 999` as unknown age in a separate category or an explicitly approved exclusion, never as a valid numeric age.

## Study and episode preflight

Before HIRA code work:

1. Read the active study instructions, SAP, code list, and `RESEARCH_LOG.md` when present.
2. Read current project HIRA/common issue sources when present; treat them as current project evidence, not bundled truth.
3. Inspect live table names, suffixes, columns, types, lengths, key coverage, missingness, and extract period with `PROC DATASETS`, `PROC CONTENTS`, or an equivalent inventory.
4. State the approved analysis grain: patient, statement, detail, episode, or another unit.
5. Confirm installed and approved SAS/R package versions and validate SAS-file compatibility in the active environment before selecting optional syntax or an R handoff path.

Before constructing an admission or treatment episode, require the SAP to define patient identity, institution continuity, allowable gap, overlap handling, and transfer handling. Do not universalize a fixed zero-day gap or one-day gap. Claims dates are not true admission/discharge dates. Report before/after count results at statement, patient, and episode grain, plus duplicate checks and duration QC.

Do not infer a table suffix, extract period, clinical code definition, delivery profile, or active-environment package version from this reference.

## Filters and code matching

- Match diagnosis codes by a clinically approved prefix or explicit subcode set. In PROC SQL use `substr(SICK_CD,1,n)`; do not use the DATA-step `=:` prefix operator there.
- Match procedure or treatment codes from the profile-verified field using a validated prefix length. Use `substr(DIV_CD,1,5)` only when the active code system and study definition support it.
- Tabulate included, excluded, unspecified, and other subcodes when an outcome rate is implausibly high or low. Compare with study-approved sanity bounds without replacing the approved definition.
- Keep domain-specific clinical definitions in the approved SAP, code list, or relevant domain reference.

## Reusable query patterns

### One-table-one-scan extraction

Build bounded patient/statement filters using the selected profile's verified keys, scan each large source table once, create all approved flags in that pass, persist reusable intermediates when project rules permit, and record row/count/key/QC checkpoints.

### Outcome and code QC

Tabulate detailed codes, inspect prevalence and missingness, verify match rates, revise only against approved evidence, and record reusable corrections through the learning contract rather than silently changing this reference.

## QC, compatibility, and R handoff

- Retain-based accumulation followed by `proc sort nodupkey` can keep the first row and discard accumulated values. Output explicitly at the intended `last.` boundary or at every approved row.
- Build raw intermediates before summaries and map dependencies before writing SQL so a summary cannot read empty or stale input.
- Run `packageVersion()` in the active environment; only when execution occurs on a server does this mean checking that active server. Use optional `ggplot2`, `scales`, or `tableone` arguments only when their installed versions are compatible and approved.
- Prefer an already verified analysis-grain SAS dataset. Only when the required packages are available, compatible, and approved in the active environment and validated SAS-file compatibility has been confirmed, read `sas7bdat` with `haven::read_sas`, use `data.table`, and avoid `%>%`; otherwise use an approved compatible handoff path.
- A historical file, copied log, acknowledgement, or absent error is not proof of current success. Use current row, key, match-rate, and output checks.
