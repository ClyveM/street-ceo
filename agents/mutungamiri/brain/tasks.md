# Mutungamiri — Tasks

## SETUP-001: Verify workspace and repo config — done

- Acceptance: VCS state known; write-safety determined without touching metadata.
- Evidence: 2026-10-29 inspection (EdenFS/Sapling metadata, no Git repo, writable).

## SETUP-002: Create AGENTS.md — done

- Acceptance: contains activation, memory, handoff, coordination, quality protocols.
- Evidence: `AGENTS.md` (11-agent roster, 10 sections).

## SETUP-003: Create 11 role.md files — done

- Acceptance: each has responsibilities, expertise, authority, dependencies, ownership.
- Evidence: `agents/*/role.md` (11 files).

## SETUP-004: Create 66 brain files — done

- Acceptance: every agent has memory, current-state, decisions, tasks,
  lessons, handoffs with truthful initial state; no fabricated history.
- Evidence: `agents/*/brain/*.md` (66 files), verified present 2026-10-29.

## SETUP-005: Create shared docs — done

- Acceptance: architecture, product-requirements, api-contracts,
  accounting-rules, voice-design, development-plan exist as truthful v0.
- Evidence: `docs/*.md` (6 files).

## SETUP-006: Create master task board — done

- Acceptance: `tasks/master-board.md` tracks setup + MVP epics honestly.
- Evidence: `tasks/master-board.md`.

## SETUP-007: Final verification and report — done

- Acceptance: 11 agents listed; brains complete; protocols verified; board exists;
  activation explained; file report delivered; no false "agents running" claim.
- Evidence: verification run 2026-10-29 (11/11 OK, 85 files); report to Owner.

## TEST-MEMORY-001: Runako memory persistence test — passed 2026-10-29

- Description: spawn Runako for a read-only summary with persisted handoff,
  verify on disk, spawn a fresh Runako with no task details, verify recovery
  from brain files alone.
- Acceptance: dated handoff + current-state persisted; fresh session recovers
  assignment ID, findings, and handoff matching disk exactly.
- Evidence: agents/runako/brain/{tasks,current-state,handoffs}.md; two real
  subagent sessions; session-2 recovery matched disk verbatim; session 1
  touched only its 3 brain files.

## MIGRATE-001: migrate to standard Git repo + worktrees — done 2026-10-29

- Description: hash-manifest + backup the source files, copy to
  C:\Users\clyve\source\repos\street-ceo, verify hashes, git init on main,
  secrets scan, initial commit, worktree probe. Old directory preserved
  untouched as fallback.
- Acceptance: manifest hashes match post-migration; git log shows initial
  commit; status clean; legacy metadata untouched; worktree probe passes.
- Evidence: manifest 85/85 + backup 85/85 + new-dir 85/85 hashes identical;
  commit 3c4e24438c5e44b494b5a0289adabcd26c1cec94 (87 files); secrets scan
  clean; worktree probe created/removed cleanly; old dir re-hash identical.