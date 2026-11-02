# Mutungamiri — Decisions

## 2026-10-29 — Team structure: 11 named agents

- Decision: Mutungamiri + Runako, Fambai, Hwaro, Inzwi, Ungwaru, Verengai,
  Dura, Chiono, Chengetai, Ruzivo with the responsibilities in the setup
  directive and each `role.md`.
- Alternatives: fewer combined roles (rejected: unclear ownership); more roles
  (rejected: coordination overhead before any code exists).
- Approval: directed by Project Owner setup instruction.
- Consequences: 11 brains to maintain; ownership map in `AGENTS.md` is binding.

## 2026-10-29 — No VCS initialization during setup

- Decision: create regular files only; leave `.hg/`, `.sl/`, `.eden/` alone;
  do not run `git init`.
- Rationale: EdenFS/Sapling mount without its CLI; blind init risks metadata damage.
- Approval: per setup directive caution; Owner to decide Git-vs-Sapling direction.
- Consequences: branching/worktree policy deferred; serialize writes until decided.

## 2026-10-29 — MVP stack as specified

- Decision: React+TS PWA, FastAPI, PostgreSQL, IndexedDB, Apo/Napo voice,
  Meta insights; no native app; demo-first sequencing.
- Approval: setup directive section 7.
- Consequences: recorded in `docs/architecture.md`; binding on scaffolding tasks.

## 2026-10-30 — Wave 1 sequencing and AI boundary

- Decision: build the deterministic, shop-scoped transaction foundation before voice or model-dependent features; activate backend, QA, Meta capability, and accounting-policy work in parallel because their write scopes are disjoint.
- Rationale: the same sale/stock/cash rules must serve touch, text, offline replay, and Apo/Napo. AI availability is still an evidence question, while the end-to-end demo must remain usable during provider failure.
- Consequences: AI returns schema-validated intent or explanations only; authorized domain services validate and commit. Voice and insight agents integrate after the contracts and accounting memo are reviewed.

## 2026-11-01 — Connected SQLite APK demo scope
Owner approved nooffline, SQLite catalogue/manual+handsfreeApo sale/stock/history with sanitized durable Muse investigation traces. Implemented one-worker snapshot transactions preserving existing API behavior. Port8001 chosen after older8000 listener discovered; preserve existingruntime/data. Phoneacceptance remains pending, not inferred from passingsoftwarechecks. Fullfinancial/accounting approval not claimed. Evidence docs/demo-mvp-verification.md.

## 2026-11-01 — Catalogue-grounded uncertain voice matching
Owner requested reasoning over imperfect recognition. Exactcommands remain deterministic; nonexact transcripts call configured Muse with bounded known catalogue and explicit quantity slots. Nonexact proposals always require spoken match confirmation before payment; missing/unknown/ambiguous baskets cannot partially post. Prices stay server-controlled. Approved implementation reviewed by Chengetai/Ruzivo; operational tracing distinguishes actual model calls from replay.

2026-11-02 STARTER-COGS: Ruzivo-approved illustrative opening costs onlyfor exact defaultdemo missingcosts withquantity0demo_seed provenance; never retroactively assigncosts tohistoricalsales. Existingknowncosts/zero/stock/prices/history preserved. docs/starter-demo-costs.md.

2026-11-02 FAST-VOICE: Ownerrejects24scriticalsellingwait. Exactuniquecatalogue+strictobservednoise proposals localwithmandatoryYes, cloud6sboundedfallback, no broaderfuzzy/fruitstripping; honestprovenance. Androidtransientnav+stableinsetownerMainActivity, officialAndroidguide consulted. Evidence docs/demo-mvp-verification.md.

2026-11-02 REPO-CLEAN: keep separatedteamapp localignored withexplicitopt-in, defaultshopbuild/API independent; preserveagentbrains andhistoricalnotes. Sourceonlyexport withfreshdependencies isdeliverygate, notdeveloperinstalledtree. Rootuserrequestedcleanup/publication. Builderbrief currentconnectedAPKscope supersedesOct29v0.
