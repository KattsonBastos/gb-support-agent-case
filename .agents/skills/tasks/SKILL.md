---
name: tasks
description: Generate an ordered, phased implementation checklist in tasks.md based on spec and plan
---

# /tasks: Phased Task Breakdown Workflow

## Objective
Break down the approved `plan.md` and `spec.md` into an actionable, dependency-ordered checklist in `tasks.md`.

## Instructions
1. **Load Context:**
   - Read active `spec.md` and `plan.md`.
   - Read `.specs/constitution.md`.
2. **Breakdown Structure:**
   Divide tasks into sequential phases:
   - **Phase 1: Foundations & Data Models:** Schemas, migrations, domain structs, and repository interfaces.
   - **Phase 2: Core Logic (Services):** Business rules, validations, error handling, and table-driven unit tests.
   - **Phase 3: Delivery (API / Handlers):** Routing, controllers/handlers, dependency injection wiring, and integration tests.
   - **Phase 4: Verification:** AC verification against `spec.md`, constitution compliance check, linter (`golangci-lint`), and `go test ./...`.
3. **Format Requirements:**
   - Every task must be an unchecked markdown item: `- [ ] Task X.Y: Description`.
   - Tasks must be small, atomic, and testable.
   - Include acceptance criteria traceability where applicable.
4. **Generate `tasks.md`:**
   - Write to `tasks.md` in the active feature directory.
