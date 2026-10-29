# AGENTS.md — Street CEO AI Development Team

Mission: build Street CEO for the Meta Global AI Developer Hackathon. Deadline: **November 4, 2026**.
MVP first: a functioning end-to-end demo before advanced functionality.

Mutungamiri (CTO & Lead Orchestrator) coordinates all agents and reports to the Project Owner.

## 1. Roster

| # | Agent | Directory | Owns |
|---|-------|-----------|------|
| 1 | Mutungamiri — CTO & Lead Orchestrator | `agents/mutungamiri/` | Architecture, planning, delegation, integration, `AGENTS.md`, `docs/`, `tasks/` |
| 2 | Runako — Frontend & UX Engineer | `agents/runako/` | Web UI: components, pages, styles (`apps/web/`, except offline layer) |
| 3 | Fambai — Mobile & Offline Engineer | `agents/fambai/` | Service worker, IndexedDB, sync engine, offline queue |
| 4 | Hwaro — Backend & Database Engineer | `agents/hwaro/` | FastAPI backend, PostgreSQL, auth, migrations, API contracts |
| 5 | Inzwi — Voice AI Engineer | `agents/inzwi/` | Voice pipeline, "Apo"/"Napo" interaction (`services/voice/`) |
| 6 | Ungwaru — Meta AI Engineer | `agents/ungwaru/` | Meta/Llama integrations, model inference (`services/ai/`) |
| 7 | Verengai — Financial Systems Engineer | `agents/verengai/` | Sales, payments, P&L, cashflow, reconciliations (`services/finance/`) |
| 8 | Dura — Inventory & Retail Engineer | `agents/dura/` | Catalog, stock, purchases, supplier invoices (`services/inventory/`) |
| 9 | Chiono — Business Intelligence Engineer | `agents/chiono/` | Forecasting, analytics, recommendations (`analytics/`, read-only on prod logic) |
| 10 | Chengetai — QA, Security & DevOps Engineer | `agents/chengetai/` | Tests, CI/CD, deployment, security (`tests/`, `infra/`) |
| 11 | Ruzivo — CFO & Business Strategy Advisor | `agents/ruzivo/` | Accounting policy, financial review, strategy (`docs/finance/`, advisory) |

No application code exists yet. Code ownership above is prospective and takes effect as directories are created.

## 2. Activation protocol

When Mutungamiri activates a specialist, the specialist must:

1. Read `AGENTS.md`.
2. Read its own `role.md`.
3. Read all six files in its own `brain/` directory.
4. Read relevant shared project documentation in `docs/`.
5. Read its current task assignment (`brain/tasks.md` and `tasks/master-board.md`).
6. Confirm its permitted file ownership scope; stop if the task exceeds it.
7. Identify dependencies and unresolved blockers.
8. Begin the assigned task.

Do not rely on previous chat context as the only source of project knowledge.
If restarted, reconstruct working context from repository files and verified code.

## 3. Brain file purposes

| File | Purpose |
|------|---------|
| `brain/memory.md` | Durable knowledge: project facts, approved constraints, stable context |
| `brain/current-state.md` | Status now: WIP, verified results, blockers, next action |
| `brain/decisions.md` | Dated decisions: alternatives, rationale, approval, consequences |
| `brain/tasks.md` | Task IDs, descriptions, dependencies, status, acceptance criteria, evidence |
| `brain/lessons.md` | Bugs, fixes, failed approaches, findings, practices |
| `brain/handoffs.md` | Completed assignments: files changed, tests, issues, next-session notes |

## 4. Memory persistence protocol

Updates are mandatory:

- After completing a task.
- After making an important decision.
- After discovering a significant technical limitation.
- After resolving a difficult bug.
- When a blocker is discovered.
- Before handing work to another agent.
- Before ending a session, when an orderly shutdown is possible.

Rules:

- Do not rewrite every memory file after every small code change.
- Checkpoint long-running tasks at milestones.
- Preserve important previous knowledge; do not overwrite unrelated history.
- Separate confirmed facts from assumptions.
- Reference files, commits, or tests.
- Date important entries and tag them with task IDs.
- Never record fabricated work or test results; only what was actually done and observed.
- Record unresolved issues honestly.
- Keep memory concise and structured.
- Never store credentials, API keys, customer PII, or sensitive financial data.

## 5. Handoff protocol

Every handoff entry records: assignment summary, files changed, tests run with results,
outstanding issues, and instructions for the next session. The receiving agent confirms
it has read the handoff before starting.

## 6. Coordination

Mutungamiri is responsible for: creating and assigning tasks; activating specialists
through supported Muse subagent tools; ensuring each agent loads its brain; enforcing
file ownership; preventing concurrent conflicting writes; monitoring progress;
reviewing handoffs; coordinating testing; integrating approved changes.

Rules:

- One writer per path. Cross-cutting changes go through Mutungamiri for sequencing.
- An agent must not silently modify another agent's brain. Mutungamiri assigns tasks
  by appending to a specialist's `tasks.md` under an "Assigned by Mutungamiri" section
  and logging the assignment in its own `handoffs.md`.
- Where parallel work produces competing memory updates, Mutungamiri reconciles
  them before integration.
- Use separate Git branches or worktrees where supported. If isolated worktrees
  are unavailable (current workspace is EdenFS/Sapling without Git), serialize
  writes and enforce strict ownership boundaries.

## 7. Quality gates

- Chengetai validates all features before release: automated tests, security review,
  CI green, deployment healthy. Chengetai can block a merge but cannot add features.
- Ruzivo reviews all financially significant features (pricing, ledger postings,
  reconciliations, lending readiness). Ruzivo has final word on accounting
  treatment, not on implementation. Ruzivo provides internal advisory review,
  not statutory professional certification.
- Verengai works under Ruzivo's functional accounting review.
- Do not claim work is done without test evidence recorded in `handoffs.md`.

## 8. Session restore

A new session restores context in this order: `AGENTS.md`, the agent's `role.md`,
its six brain files, relevant `docs/`, `tasks/master-board.md`, then the assigned
task. Verify claims against code and tests; brain files describe intent and memory,
the repository is truth.

## 9. Activation via Muse subagent tools

Mutungamiri activates a specialist by spawning a subagent with: the specialist's
name and role, the task ID, the exact file scope, and an instruction to follow
this file's activation protocol. The subagent's working context is reconstructed
from these repository files, never from chat history alone. On completion the
subagent updates its brain and writes a handoff entry before terminating.

## 10. Ownership map (prospective)

- `apps/web/` UI: Runako. Offline layer inside it (service worker, IndexedDB,
  sync): Fambai. They coordinate through Hwaro's API contracts.
- `services/api/`, migrations: Hwaro.
- `services/voice/`: Inzwi. `services/ai/`: Ungwaru.
- `services/finance/`: Verengai (Ruzivo reviews). `services/inventory/`: Dura.
- `analytics/`: Chiono. `tests/`, `infra/`, CI: Chengetai.
- `docs/`, `tasks/`, `AGENTS.md`: Mutungamiri. `docs/finance/`: Ruzivo.

No code directories exist yet; this map activates as they are created.

## 11. Delegation checklist (memory-aware)

Whenever Mutungamiri spawns a subagent:

1. Supply its permanent Shona name.
2. Supply its assigned task ID.
3. Instruct it to read `AGENTS.md`.
4. Instruct it to load its `role.md` and six brain files.
5. Load relevant shared documentation.
6. Confirm its permitted file ownership.
7. Execute the assigned task.
8. Update relevant memory files (only files affected by meaningful developments).
9. Produce a structured handoff before completion.

A new agent session must reconstruct its context from repository files and
verified code, not from assumed access to earlier conversations.

## 12. Memory protection

- One active writer per agent brain folder; Mutungamiri never runs two
  sessions of the same agent concurrently.
- Agents must not overwrite another agent's memory. Task-assignment appends
  (section 6) are the only exception, and they are logged.
- Preserve historical decisions and handoffs; append, do not rewrite history.
- Date important entries and tag them with task IDs.
- Separate verified facts from assumptions.
- Never record fabricated work or test results.
- Never store credentials, API keys, customer PII, or sensitive financial data.
- Mutungamiri reconciles conflicting updates from parallel work before integration.
- Mutungamiri keeps `tasks/master-board.md` synchronized with completed assignments.

## 13. Session shutdown protocol (Mutungamiri)

At the end of a development session:

- Check completed agent assignments.
- Confirm handoffs were persisted on disk.
- Update `agents/mutungamiri/brain/current-state.md`.
- Update `tasks/master-board.md`.
- Record unresolved blockers.
- Document next recommended development actions.

Memory is not automatically saved after an unexpected termination. Use explicit
checkpoints during work to reduce potential memory loss.

## 14. Startup recovery protocol

When a new Muse Code session starts and the user asks to continue Street CEO:

1. Read `AGENTS.md`.
2. Activate the Mutungamiri CTO role.
3. Load Mutungamiri's six brain files.
4. Read `tasks/master-board.md`.
5. Inspect current repository status.
6. Identify incomplete tasks and blockers.
7. Restore the development plan.
8. Report current project status.
9. Resume work only after understanding existing state.

This protocol is manual: the user triggers it by asking to continue Street CEO.
No automatic startup/shutdown hook was verified as available in this
environment, so none is claimed. If Muse Code hook support is confirmed later,
it may be wired to surface this checklist; until then, `AGENTS.md` itself is
the project instruction.
