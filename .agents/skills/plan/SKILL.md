---
name: plan
description: Formulate technical architecture and design in plan.md conforming to the constitution
---

# /plan: Technical Implementation Plan Workflow

## Objective
Translate the approved requirements in `spec.md` into a concrete architectural blueprint in `plan.md`.

## Instructions
1. **Load Context:**
   - Read the active `spec.md`.
   - Read `.specs/constitution.md` thoroughly (adhere strictly to tech stack, layered architecture, DI, and error handling rules).
2. **Design Solution:**
   - **Architecture & Approach:** Map out affected packages, services, handlers, and repositories.
   - **Data Models & Schema Changes:** Define Go structs, database schema/migrations, and state modifications.
   - **Interfaces & Endpoints:** Detail interface definitions, function signatures, HTTP routes, and request/response payloads.
   - **Testing Strategy:** Specify how unit tests (table-driven), mock interfaces, and integration tests will prove the Acceptance Criteria.
3. **Generate `plan.md`:**
   - Write the finalized technical plan into `plan.md` in the active feature directory.
4. **Human Review Gate:**
   - Ask the user to review the architectural choices and sign off before running `/tasks`.
