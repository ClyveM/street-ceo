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
