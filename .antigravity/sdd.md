---
description: Spec-Driven Development (SDD) Workflow Rules
globs: *
alwaysApply: true
---

# Spec-Driven Development (SDD) Rules

## Active Specification
- **Spec Directory:** `None`
- **Spec ID:** `None`
- **Feature Name:** `None`
- **Constitution:** `.specs/constitution.md`


> **Note:** No active feature specification selected. Run `ksdd sync <spec-folder>` to select an active spec.

## SDD Workflow Commands
When instructed by the user, execute according to these standardized workflows:
- **`/specify`**: Elicit requirements, clarify edge cases, and generate/update `spec.md`.
- **`/plan`**: Translate `spec.md` into concrete architecture, data models, and testing strategy in `plan.md`.
- **`/tasks`**: Break down `plan.md` into an ordered, testable checklist in `tasks.md`.
- **`/implement`**: Sequentially execute unchecked tasks `[ ]` from `tasks.md`, test each, and check off `[x]`.

## Core Principles
1. **Constitution First:** Always comply with architectural boundaries, libraries, error handling, and testing policies defined in `.specs/constitution.md`.
2. **Spec Boundaries:** Deliver only what is defined in the active specification (`spec.md`). Do not implement features outside the defined scope.
3. **Plan Compliance:** Respect the design, data models, and interface contracts agreed in `plan.md`.
4. **Task-by-Task Execution:** Follow `tasks.md` sequentially. Complete all tasks within Phase N and mark them `[x]` before progressing to Phase N+1.
5. **No Hallucinations:** Never assume unwritten requirements or silent failures. Clarify ambiguities with the user.
