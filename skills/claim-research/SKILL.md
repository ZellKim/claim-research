---
name: claim-research
description: Use when working on NHIS/국민건강보험공단 or HIRA/심평원 claims-data SAS/R extraction, analysis, errors, cohort construction, QC, or research workflow.
---

# claim-research

## Trigger and scope

Apply this skill to NHIS or HIRA claims-data research and to SAS/R extraction, analysis, error correction, cohort construction, and QC. Current project `AGENTS.md`, `CLAUDE.md`, approved study documents/SAP, active schema, and current environment evidence outrank this reusable skill and generated knowledge.

## Select the source route first

Before selecting variables, select exactly one route:

1. **HIRA/심평원** for HIRA extract or analysis.
2. **NHIS Wonju/on-site extraction** for secure-center server extraction.
3. **NHIS post-extract analysis** for provided SAS tables processed inside the secure environment or an approved exported layout. Record which delivery stage applies; provided SAS tables do not imply export permission or a universal schema.

Never mix tokens, table semantics, dates, credentials, extraction commands, or privacy assumptions across routes. If the source or phase is ambiguous, stop before selecting variables and ask for the source, environment, active inventory, study instructions/SAP, extract period, and analysis grain. Continue work that does not depend on those answers, such as reviewing available instructions or preparing the QC outline; do not invent the missing study definitions or schema. Never perform a global search-and-replace between NHIS and HIRA tokens.

## Start with authority and evidence

1. Read the current project instructions and approved study documents/SAP.
2. Inspect the active schema and current environment evidence before assuming a table, variable, type, or phase.
3. Read [references/guardrails.md](references/guardrails.md) before mapping fields or writing extraction/analysis code.
4. Use generated knowledge only for the selected route and recorded scope. Current evidence outranks generated knowledge.

## Read applicable code-generation guidance

Before creating or revising NHIS/HIRA SAS/R code, select the source route above, then read the applicable guidance in this order:

1. **Current project:** follow its designated coding instructions and `code_generation/README.md` when available. Current user decisions, approved study documents/SAP and active schema retain priority.
2. **Available maintained library:** if the installed skill has a readable `runtime-context.json`, use its `canonical_package_root` only as a locator. When reading a canonical skill directly, identify the package root containing `skills/` and `research_learning/`. Check whether `claim_data_with_claude/claims-research-plugin/code_generation/` actually exists beside that package under their common parent, and read its current README if accessible. Do not assume another PC has that layout or search the entire Drive.
3. **Portable bundle:** when no applicable local library is available, read [references/code-generation_20261111.md](references/code-generation_20261111.md) relative to this skill. A portable installation does not require runtime context, a learning engine, a particular drive letter or the original research-example folders. Record which guidance was used; the dated bundle is a reviewed snapshot, not a claim to be the latest local library.

An unreadable project-mandated reference is still missing evidence: identify the specific path and affected decision. Use available guidance for independent work while resolving that dependency. Ask for missing SAP definitions, schema, period, grain or other required study inputs before implementing decisions that depend on them.

### Select only resources for the chosen route

- **HIRA:** use the portable guide's HIRA requirements and drafting structure. If a maintained library is available, `sas_templates/00_HIRA_initial_extract_template.txt` is an optional historical reference only after verifying the current environment and instructions; its study constants, deletion/export steps and older structure are not defaults.
- **NHIS Wonju:** use the portable guide's Wonju requirements and drafting structure. The local `sas_templates/10_NHIS_wonju_extract_template.txt` is an optional Tibero/ODBC reference only after current environment, request contract and study settings are confirmed. Do not apply it to provided SAS tables.
- **NHIS provided SAS tables:** first read the applicable project style reference or the bundled [concise SAS style example](assets/reference_code_style/nhis_sas_style_20261111.txt). It shows short purpose comments, visible SQL/DATA blocks, nearby QC and small macros for actual repetition. For additional error-stop and progress/QC mechanics, consult [the SQL/QC example](assets/sas_templates/30_NHIS_proc_sql_block_qc_template.txt) as needed. Both use synthetic WORK data and supply no study definitions or verified schema. The large historical Word and its reading parts are optional local references; never require or load all parts for routine drafting. The local `20_NHIS_post_extract_subset_template.txt` has older wrappers; current block/restart rules take precedence and it is not part of this bundle.
- **R:** first read the applicable project style reference or the bundled [concise R style example](assets/reference_code_style/nhis_r_style_20261111.R), alongside the guide's condition-by-condition assignment rules. The example uses synthetic in-memory data and `data.table` to show visible steps, key/join QC, explicit `:=` assignments, preserved unknowns and denominators. It supplies no NHIS schema or study definitions. Original local R scripts, including the Jeong reference, and `project_templates/` are optional detail for the requested analysis; matching, KM/Cox, endpoints, covariates and thresholds require the current SAP. Routine drafting does not require loading the full original scripts.

Reuse suitable existing extracts before supplementing missing rows/columns, preserve the candidate population and study windows, and keep creation, immediate QC and restart boundaries visible. Templates do not supply the study's clinical definitions, constants, paths or verified schema.

### Check the exact delivery set

Prefer the current project's approved SAS checker, including a maintained library explicitly designated by that project. Otherwise use [scripts/validate_sas_preflight.py](scripts/validate_sas_preflight.py) relative to this skill on the exact SAS/TXT delivery set. Retain input/annotated pair comparisons and previously reviewed hash-manifest checks where applicable. Resolve errors and record the applicability of review findings; do not replace study-specific checks with the bundled checker.

The checker performs static SAS checks; it does not run SAS/R, inspect real research data or validate study results. Record separately which static, mock, runtime and real-data checks were performed. If a required checker, runtime or input is unavailable, name the missing item, keep its dependent verification pending and continue independent work.

## Route static references

- After the HIRA route is selected, read [references/hira-semantic-layer.md](references/hira-semantic-layer.md) for HIRA table, variable, join, or code-matching detail. For any reusable HIRA fact, read [references/hira-evidence.md](references/hira-evidence.md) and revalidate it against the active schema, study SAP, current issue sources, and current environment. Never load or apply the HIRA semantic/evidence files on an NHIS route.
- After either NHIS route is selected, read [references/nhis-semantic-layer.md](references/nhis-semantic-layer.md) for that phase's tables, fields, and delivery boundaries. After NHIS is selected, read [references/nhis-evidence.md](references/nhis-evidence.md) before relying on or updating a reusable NHIS fact, then revalidate it against the active inventory/layout, approved request contract, study SAP, and current environment. Never load or apply the NHIS semantic/evidence files on a HIRA route.
- Read [references/common-code-qc.md](references/common-code-qc.md) only when the work involves SAS/R code, joins, QC, output, publication, or analytic-validity checks.

Verify `PROC CONTENTS` or an equivalent inventory, types, lengths, missingness, cardinality, and match rates before mapping names. Require explicit clinical definitions and analysis grain. Preserve raw-before-summary dependencies, bounded scans, progress output, and QC checkpoints.

## Enforce executable output QC

For any task that reviews, finalizes, regenerates, or releases a report, table, CSV/XLSX, SAS/R result, or an unexpectedly small or large value, read [references/common-code-qc.md](references/common-code-qc.md) and apply its executable output-QC gate automatically. Do not wait for the user to name or request the validator.

- Discover the current project's approved plausibility validator and study contract; prefer the repository's canonical implementation over ad hoc arithmetic.
- Run an eligible contract with diagnostic output in a temporary or task-local path that does not overwrite study artifacts.
- Never treat a test fixture, missing production contract, missing authoritative aggregate, or missing independent approval registry as release evidence.
- Treat every nonzero release-gate result as release-blocking while continuing the document-to-code-to-data lineage review.
- Do not let the executable gate replace definition, denominator, period, grain, provenance, or causal-interpretation checks.

## SAS incident closure and prevention

For SAS error or warning work, update the existing project research log and error catalogue before closing the task: record the sanitized signature, evidence, confirmed cause versus uncertainty, applicability, minimal correction, regression check, and verification status. Reuse the existing issue ID for recurrences. Generalize language/runtime patterns; keep study definitions, server paths and patient/claim details local.

Before writing or delivering another SAS script, consult the relevant project issue IDs and SAS guidance, then apply the checker selection and exact-delivery-set checks above. Include input/annotated pairs and the previously reviewed hash manifest where available. Resolve errors and document the applicability of review findings. Preserve the project's analysis and split-order tests; a static checker is not SAS execution or real-data validation.

For a new mechanically detectable failure, add a failing case and valid counterexamples to the existing checker/tests. When common enforcement would be misleading, keep a project-specific check and record why. Distinguish observed errors from preventive risks, and mark runtime/real-data verification pending until evidence arrives. Do not regenerate a baseline hash merely to silence drift. This is a task-time workflow, not a background watcher or an automatic promotion of research knowledge.

## Decide whether to learn

After a reproducibly verified correction or potentially reusable discovery, read [references/learning-contract.md](references/learning-contract.md). Use managed capture only when its runtime context, canonical engine and authorization are available; use profile `nhis-hira` and the exact machine fields. In a portable-only installation, keep sanitized lessons in the existing project research log without capture, promotion, synchronization or automation. If privacy, provenance, route or required metadata is uncertain, refuse capture and keep the lesson local/unpromoted.

Human-authored content and static guardrails are never auto-rewritten. The five semantic/evidence/common files—HIRA semantic, HIRA evidence, NHIS semantic, NHIS evidence, and common code/QC—are human-authored static references and are never automatically rewritten. Generated knowledge stays only in the three renderer-owned references, not in this marker block or any static reference.

## Route generated knowledge

- Read [references/learned-code-fixes.md](references/learned-code-fixes.md) for verified low-risk compatibility fixes that match the current environment.
- Read [references/verified-discoveries.md](references/verified-discoveries.md) for source-approved facts within their recorded version, date, route, and scope.
- Read [references/workflow-lessons.md](references/workflow-lessons.md) for staged or reviewed process lessons; revalidate them against current evidence.

## Protected proposal block

Only the proposal integrity gate may stage bounded learned bullets between these markers. Never place renderer-owned generated knowledge here and never adopt a proposal automatically.

<!-- SKILLOPT-SLEEP:LEARNED:START -->
<!-- SKILLOPT-SLEEP:LEARNED:END -->
