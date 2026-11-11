# Common SAS/R code and QC

This source-neutral, human-authored static reference is never auto-rewritten or automatically rewritten. Load it only for applicable SAS/R implementation, joins, QC, output, publication, or analytic-validity work; source-specific semantics still come from the selected route.

## SAS and SQL safeguards

- Use explicit aliasing for identically named join columns; state which source owns each selected key or value.
- The DATA-step `=:` operator is unavailable in PROC SQL. Use a verified alternative such as `substr`.
- Stage `CALCULATED` expressions and denominator logic before aggregation or summarization to avoid SQL remerge ambiguity.
- Avoid FROM-less literal-only or scalar SELECT statements when SAS environment compatibility is uncertain.
- For open-code `%IF` or `%ABORT`, verify support in the active SAS environment before use.
- Respect the 32-byte SAS member-name limit.
- `PROC APPEND FORCE` has a thin-first schema/drop risk: a thin first table can define the target and drop incoming columns. Initialize the target from the first-real full-schema table, or predeclare the full target schema, and inspect logs.

## Publication and structural QC

- A publication manifest records `exists`, `nobs`, `nvars`, an explicit zero-row policy, and `RUN_ID`.
- Report join coverage, orphan records, row inflation, and split QC; investigate unexpected loss, multiplication, or partition disagreement.

## Executable cross-output plausibility gate

Apply this gate automatically when reviewing or releasing claims-research reports, tables, spreadsheets, or statistical outputs. The user does not need to name the validator.

1. Discover the project-provided canonical validator, contract schema, study contract, aggregate manifest, and release runner. A common repository location is `code_generation/qc/validate_plausibility.py`; do not assume the path if current project evidence differs.
2. Check whether the study contract covers the current route, extract/cohort version, artifact version, grain, period, metric definition, deduplication, and unit. A historical contract does not validate a newer artifact.
3. Run the validator automatically when an eligible contract and aggregate-only inputs exist. Write machine output only to a temporary or task-local diagnostic path; do not overwrite source reports, reviewed tables, or code.
4. Use test mode only for an explicitly marked test fixture. Never promote its result to production release evidence.
5. Require the project-defined independent approval registry and trusted key for production release when the validator contract requires them. Do not mint, edit, self-approve, or substitute these records.
6. Interpret the canonical exit contract: zero may proceed to the remaining checks; any nonzero result blocks release. `REVIEW_REQUIRED` is not automatic proof of an error, but it is not a pass.
7. If the production contract, authoritative aggregate, or approval registry is absent, record the executable gate as not completed and block a release-ready claim. Continue the manual cross-check and identify the exact missing asset.
8. Preserve the separate document-to-CSV-to-code lineage audit. The executable gate supplements, rather than replaces, definition, denominator, period, grain, subset, provenance, and causal-interpretation review.

## Analytic-validity safeguards

- Use approved ingredient/code token whitelists for drug mapping, not substring inference, and preserve combination ingredients.
- Map ICD/KCD chapter ranges with explicit ordered ranges and report unmapped-code QC.
- Any estimand change requires cohort and comparator revalidation plus benchmark and plausibility QC.
- Apply R `p.adjust` after subset selection for the intended testing family.
- Detect and handle a single-level binary outcome before modeling.

Do not copy issue narratives, exact clinical lists, study results, raw rows, identifiers, credentials, paths, logs, or unrestricted command output into this reference.
