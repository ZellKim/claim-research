# NHIS semantic layer

Read `guardrails.md` first. This human-authored static reference applies only after an NHIS route has been selected and is never auto-rewritten or automatically rewritten. Never apply it to a HIRA route. Current project instructions, approved study documents/SAP, the active inventory/layout, approved request contract, and current environment evidence are final authority.

## Keep the two NHIS phases separate

NHIS Wonju/on-site extraction from live `HBMT_TBGJME20/30/40/60` tables is distinct from approved post-extract BFC/DTH/T20/T30/T40/T60 analysis. Never project a field, key, library, account, or operational rule from one phase into the other. Verify the active inventory/layout and approved request contract before selecting fields or joins.

`HBMT_TBGJME20/30/40/60`, `USRTMP`, and medication de-duplication guidance are scoped/versioned observations from the Wonju/on-site researcher-extraction system and require live revalidation. Never apply or project those Wonju assumptions to Myeongdong/명동 analysis: Myeongdong uses a different table and database system. Verify its own project instructions and active inventory instead.

Myeongdong/명동 is an environment or location label, not an NHIS route selector. Never infer or select the standard post-extract route or its 2026 layout from that location alone; first confirm the delivery phase/type, active inventory, and approved request contract.

Provided SAS tables processed inside the secure environment and approved exported analysis files are different delivery stages within the provided-table/post-extract route. Record the actual stage, input layout, and permitted outputs. Neither stage establishes the 2026 profile below without current study evidence, and neither authorizes moving detailed records outside the secure environment.

## Verified 2026 post-extract profile

The following standard delivered column counts are versioned 2026 observations, not a universal NHIS schema:

| Group | Columns | Key observations |
| --- | ---: | --- |
| BFC | 12 | `INDI_DSCM_NO` |
| DTH | 2 | `INDI_DSCM_NO`, `DTH_ASSMD_DT` |
| T20 | 28 | `CMN_KEY`, `INDI_DSCM_NO`, and delivered dates |
| T30 | 12 | `CMN_KEY`; no patient ID in the standard exported layout |
| T40 | 5 | `CMN_KEY`; no patient ID in the standard exported layout |
| T60 | 8 | `CMN_KEY`; no patient ID in the standard exported layout |

T30/T40/T60 use `CMN_KEY` and may omit the patient identifier in this standard exported layout. Recover patient identity only through verified linkage to T20. Inspect the actual delivery before `KEEP=` lists, joins, or field-dependent logic.

## Application workbook as the data-request contract

Treat the approved application/data-request workbook as the extraction contract. It must distinguish “only qualifying claim rows” from “all claims for defined people,” list explicit years and variables, and put additional tables through documented justification and review. Do not silently assume either delivery mode or add unapproved data.

Specialized screening schema is year-dependent and request/version dependent. `EXMD_BZ_YYYY` versus `HC_BZ_YYYY` is a versioned example of name variation, not a universal field list.

## Scoped on-site operational observations

SQL-only execution and USRTMP overwrite, case, and quota constraints are scoped/versioned on-site observations requiring live revalidation. They do not describe post-extract SAS/R.

Conditional `FORM_CD` medication de-duplication is also a scoped/versioned observation requiring live revalidation: T20 includes 20 and 21; T40 includes 20 and 21; T30 includes 20; T60 excludes 20 and 21. Apply it only when the active on-site contract confirms the same rule.

Never apply or project this Wonju `FORM_CD` rule to Myeongdong/명동 analysis.

Keep extraction simple, bounded, quota-aware, resumable, and independently verifiable. Never hard-code credentials, accounts, DSNs, researcher paths, or USRTMP names.
