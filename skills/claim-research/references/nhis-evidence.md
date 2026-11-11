# NHIS semantic evidence

This human-authored static evidence register is never auto-rewritten or automatically rewritten. It records source observations, not runtime dependencies or universal schema claims.

## Wonju-only training scope

`연구자 추출 이론 교육 자료_260514.pdf` documents NHIS Wonju researcher extraction/on-site only. Do not apply or project it to Myeongdong/명동 analysis: Myeongdong uses a different table and database system. Myeongdong is not a route selector and never establishes the post-extract route or 2026 layout by itself. Every page locator from that PDF below inherits this Wonju-only boundary.

## Evidence register

- Exact-duplicate layout workbooks: `NHIS_맞춤형 자료 제공 컬럼 레이아웃_2026_v1.xlsx` and `맞춤형 자료 제공 컬럼 레이아웃_260325.xlsx`; modified 2026-03-25; SHA-256 `6B19A9756B43D8C23B0A9A9EF6593B7A779BF3419307F31DD59AE7F33661D92A`. Record them as one evidence item because their content is identical.
- Extraction-contract workbook: `customized_DB_application_2026.xlsx`; modified 2026-04-21. It governs requested population/claim mode, years, variables, and reviewed additional tables.
- Specialized screening workbook; dated 2026-05-27. Treat its screening field names as year/version/request-dependent evidence.
- `연구자 추출 이론 교육 자료_260514.pdf` (260514 version) p31: scoped evidence for SQL-only execution and USRTMP overwrite/case/quota constraints; require live revalidation.
- `연구자 추출 이론 교육 자료_260514.pdf` (260514 version) p13: scoped evidence for conditional `FORM_CD` duplicate prevention; require live revalidation.
- `연구자 추출 이론 교육 자료_260514.pdf` (260514 version) p45: example that on-site T20 includes `INDI_DSCM_NO` availability that must not be projected into a different post-extract layout.
- `연구자 추출 이론 교육 자료_260514.pdf` (260514 version) p52: example that on-site T40 includes `INDI_DSCM_NO` availability that must not be projected into a different post-extract layout.

## Excluded from NHIS semantics

- Exclude `분석사례 소개(실습).pdf` from NHIS claims semantics: it is a misfiled HIRA source using T200/T300/T400/T530.
- The 2017 NHIS sample-cohort document does not support inferring a current 2026 customized DTH cause-of-death field.
- Exclude `CohortMethod R분석 가이드.pdf` from NHIS claims semantics: it is OHDSI/CDM material and only a later candidate for `$cdm-research`.

## Evidence boundary

Revalidate every fact against the active on-site inventory or delivered post-extract layout, the approved request contract, and the study SAP. Do not bundle exact machine paths, credentials, patient/claim rows, identifiers, small-cell output, raw logs, or unrestricted command output. Update this file only through human review of authoritative, privacy-safe evidence.
