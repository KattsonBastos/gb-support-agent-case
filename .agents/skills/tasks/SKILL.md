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
   - **Phase 1: Foundations & Data Models:** Pydantic schemas, `AgentState` fields, `Settings` entries, mock data / catalog files.
   - **Phase 2: Core Logic (Tools, RAG & Graph):** `@tool` functions with pure `_core()` logic, retriever changes, graph nodes/edges, prompts and guardrails, with `pytest` unit tests (prefer `@pytest.mark.parametrize`).
   - **Phase 3: Delivery (API / Frontend / Infra):** FastAPI routes and SSE streaming, Streamlit changes, observability wiring, Docker/compose updates, and integration tests with `TestClient`.
   - **Phase 4: Verification:** AC verification against `spec.md`, constitution and guardrails compliance check (PII isolation, commercial secrecy, SSE format), and a green `pytest` run without network/API keys.
3. **Format Requirements:**
   - Every task must be an unchecked markdown item: `- [ ] Task X.Y: Description`.
   - Tasks must be small, atomic, and testable.
   - Include acceptance criteria traceability where applicable.
4. **Generate `tasks.md`:**
   - Write to `tasks.md` in the active feature directory.
