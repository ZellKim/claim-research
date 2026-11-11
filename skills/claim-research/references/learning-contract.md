# NHIS/HIRA learning contract

This contract records reusable corrections without treating conversational memory as evidence. Human-authored content and static guardrails are never auto-rewritten.

## Check whether managed learning is available

This skill also works as a portable code-writing and QC bundle. Managed learning is optional and requires a valid, readable `runtime-context.json` identifying the existing canonical package, its available learning engine and authorization to write the intended learning state. Check those conditions before creating an event or running an engine command.

If context, engine or authorization is absent, stale or inaccessible, use the existing project research log for sanitized local lessons. Do not run capture, promotion, cycle, runtime synchronization or automation, and do not create guessed package paths, substitute context metadata or learning state inside the installed skill. Continue the research task using the portable guidance; missing managed learning is not a reason to require an unavailable Drive library. Apply the same privacy and evidence rules to local log entries.

## Capture only a validated event

When managed learning is available and authorized, after a reproducibly verified correction create a privacy-safe structured event for profile `nhis-hira`. Validate the complete object before capture. Use the exact machine event fields; do not rename or substitute event fields with conversational aliases:

- Common fields: `schema_version` (exactly `1`), a new UUID `event_id`, `profile`, `kind`, `summary`, `data_classification`, `status`, and timezone-aware `created_at`.
- Privacy object: `privacy` containing `contains_personal_data`: `false` and `contains_credentials`: `false`.
- A `kind: code_fix` event also requires non-empty `error_signature`, `root_cause`, `fix`, and `applicability` objects; `risk_level`; `knowledge_scope`; and `verification` containing Boolean `passed`, non-empty string array `commands`, and bounded string `evidence`.
- A `kind: discovery` event requires `provenance` with `source_type` and `reference`, plus `approval` with `source_verified`, `approved_by`, and `approved_at`.

Missing required metadata means do not create a structurally invalid substitute event. Ask for the missing bounded metadata and keep the lesson local until it validates before capture.

## Persist through the canonical engine

A managed runtime copy has `runtime-context.json` beside `SKILL.md`; a portable installation need not have it. Read only its `canonical_package_root` value to locate the existing canonical package, verify the engine and authorized state location, and apply the availability gate above. Do not guess a different package or write learning state into the runtime mirror.

Only after that gate passes, create one complete, explicit event JSON file under `<canonical_package_root>/inbox/`. Never scan a transcript, chat history, research directory, patient/claim source, or log to manufacture event files. Run `<canonical_package_root>/scripts/research-learning.ps1` with the `capture --file <absolute-event-file>` arguments after validation. The operator may run `<canonical_package_root>/scripts/run-nightly.ps1 -Root <canonical_package_root> -Inbox <canonical_package_root>/inbox` to execute the bounded `cycle` over that explicit inbox. The nightly cycle promotes only policy-eligible records and stages reviewed SkillOpt tasks; it does not call SkillOpt, a model, a research system, proposal adoption, or runtime sync.

## Apply the promotion boundary

Only passed, low-risk `code_compatibility` fixes can auto-promote. Failed, incomplete, medium/high-risk, workflow, domain, or ambiguous corrections remain staged.

Classify new source, table, or domain information as a `discovery`. Promotion requires authoritative provenance, version/date/scope, and explicit source approval. One-session suffixes and study-specific clinical rules remain staged/local. Workflow lessons remain staged. Static privacy, source-routing, and medical guardrails never auto-update.

SkillOpt never harvests raw transcripts and never auto-adopts. A reviewed proposal remains staged until its integrity gate and human review succeed.

## Refuse unsafe capture

Do not read, copy, display, or learn from raw patient/claim rows, direct or indirect identifiers, hashed IDs, raw logs, small-cell counts, credentials, exact researcher/server paths, or unrestricted command output. Hashing an identifier does not make it safe for learning.

Keep outputs aggregate and suppress them according to current project/institutional rules. Do not invent a universal threshold. If privacy or provenance is uncertain, refuse capture and keep the lesson local/unpromoted. Do not persist credentials, account values, DSNs, server inventory, exact paths, or free-form logs.

## Use generated output conservatively

- Treat `learned-code-fixes.md` as environment-constrained compatibility history.
- Treat `verified-discoveries.md` as approved facts only inside the recorded source, version/date/scope, and route.
- Treat `workflow-lessons.md` as staged or reviewed process guidance, never proof of a current schema or study rule.

Current project evidence outranks generated knowledge.
