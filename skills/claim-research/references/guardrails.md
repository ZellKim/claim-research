# NHIS/HIRA research guardrails

Current project `AGENTS.md`, `CLAUDE.md`, approved study documents/SAP, active schema, and current environment evidence outrank this reusable skill and generated knowledge.

## Route before variable selection

Before selecting or choosing any variables, select exactly one route. Never mix tokens, table semantics, dates, credentials, extraction commands, or privacy assumptions across routes, and never use a global search-and-replace to translate NHIS tokens into HIRA tokens or the reverse.

### Route 1 — HIRA/심평원

Use this route for HIRA extract or analysis with `T200`, `T300`, `T400`, and `T530`. Identify the delivery profile before field mapping. Active `PROC CONTENTS` or an equivalent delivered-layout inventory is always the final authority; never translate field names mechanically across profiles.

#### Verified 2025Q4 customized/full extract profile

This profile describes a verified delivered layout, not every HIRA delivery:

- T200 may contain direct `JID` and `MID`; it is the observed date source, with `RECU_FR_DD` stored as character `YYYYMMDD`.
- T300 may contain direct `JID` and `MID` and uses `DIV_CD`.
- T400 may contain direct `JID` and `MID` and uses `SICK_CD`.
- T530 may contain direct `JID` and `MID` and uses `DIV_CD` plus `MEFT_DIV_NO`.
- In this customized/full profile only, an already period-limited T400 extract may be deduplicated or counted directly by `JID` and `MID`. Join T200 only when dates, narrower periods, follow-up, costs, visit form, or statement-only variables are needed.

#### Historical official NPS/patient-sample profile

This historical profile uses statement identifier `SPEC_ID_SNO`. T300 may lack `JID`; T400 may lack `JID`; and T530 may lack `JID`. Patient-level detail, diagnosis, or prescription linkage may therefore require verified T200 linkage when the delivered sheets omit the patient key. Medication variables can include `GNL_NM_CD`. Active `PROC CONTENTS` or an equivalent delivered-layout inventory remains the final authority; do not treat this historical profile as current or universal.

- Parse and derive dates once in STEP 0 when the selected profile provides the required date field.
- Verify the actual table suffix in the active server or study. Never globalize one observed suffix.
- Apply one-table-one-scan to large raw tables. Build raw intermediates before summaries, convert dates once, use safe hash/filter patterns, add `%put` progress, and record row/count/key/QC checkpoints. Persistent intermediates should prevent needless rescans when project rules permit.
- In PROC SQL, use `substr(SICK_CD,1,n)` or another validated match. Do not use `=:` in PROC SQL. Require study-approved clinical code definitions and explicit analysis grain.

#### HIRA episode construction

Before constructing admission or treatment episodes, require the SAP to define patient identity, institution continuity, allowable gap, overlap handling, and transfer handling. Do not universalize a fixed zero-day gap or one-day gap. Claims dates are not true admission/discharge dates. Record before/after count results at statement, patient, and episode grain, and complete duplicate checks and duration QC.

### Route 2 — NHIS Wonju/on-site extraction

Use this route for secure-center extraction only after verifying the current Tibero/ODBC pass-through and live `HBMT_TBGJME20/30/40/60`-style inventory.

- Treat Wonju researcher-extraction training as Wonju/on-site evidence only. Myeongdong/명동 analysis uses a different table and database system; never carry Wonju table or DB assumptions into it.
- Treat Myeongdong/명동 as a location or environment label, not a route selector. Confirm the delivery phase/type, active inventory, and approved request contract before choosing an NHIS route or layout.
- Never assume post-extract SAS libraries. Never hard-code credentials, account values, or DSN.
- Keep on-site extraction simple, resumable, quota-aware, and bounded. Separate extraction from analysis.
- Verify the live table inventory, column types, date layout, key coverage, row limits, and destination rules before constructing pass-through SQL.

### Route 3 — NHIS post-extract analysis

Use this route for provided SAS tables processed inside the secure environment or an approved exported layout. Record the delivery stage and permitted outputs; server-provided SAS files do not imply authorization to export detailed data. The documented delivered profile uses patient `INDI_DSCM_NO`, claim `CMN_KEY`, monthly `T20/T30/T40/T60`, `BFC`, `DTH`, and separately approved `health screening` files. Verify every study-specific delivered layout rather than selecting fields from the location or file format alone.

- Standard T40 may not contain `INDI_DSCM_NO`; obtain patient identity through verified `CMN_KEY` linkage to T20. Study-specific T40 extracts may omit standard or request-dependent columns, so inspect the active layout before `KEEP=` or joins.
- Treat DTH as death-date and all-cause censoring by default. Do not infer cause-specific death unless an explicitly approved cause-of-death field/file and layout are confirmed.
- HbA1c is not a default general-screening item. Do not create it as a covariate/outcome without verified approved availability.
- Never insert Wonju ODBC/account/USRTMP assumptions into post-extract SAS/R. Separate extraction from analysis.

### Route 4 — NHIS design/application before delivery

For document-backed requirements or shared-reference organization, follow [research-design_20261111.md](research-design_20261111.md). Read available study instructions, codebooks, applicable year-specific layouts and forms used as reference. Record source sheet/cells; when no application is in progress, request status is not applicable rather than missing approval. Actual application work additionally compares the study's request selections and approval evidence, separately from actual delivery. Live SAS inventory is not required to draft sourced candidates; it is required before those candidates become executable field mappings. Missing evidence leaves only the dependent item pending. Choose route 2 or 3 when moving to executable code.

## Stop on ambiguity

If source or phase is ambiguous, stop before selecting variables for execution. Inspect available project evidence first, then ask only for unresolved source, environment, active inventory, study instructions/SAP, extract period or analysis grain needed by the current step. Verify `PROC CONTENTS` or an equivalent inventory, types, lengths, missingness, cardinality, and match rates before mapping executable fields. The pre-delivery design route permits sourced candidate tables without claiming actual availability.

## Revalidate every generated lesson

Use generated references only as leads within their recorded route and scope. Current evidence outranks generated knowledge. Recheck schemas, suffixes, package behavior, code definitions, privacy requirements, and QC before acting.
