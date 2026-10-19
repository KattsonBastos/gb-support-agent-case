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
   - Read `.specs/constitution.md` thoroughly (adhere strictly to the tech stack, layer boundaries in `src/`, guardrails, error handling and testing rules).
   - Read related ADRs in `docs/adrs/` and plans of dependent RFCs in `.specs/RFC-*/plan.md`.
2. **Design Solution:**
   - **Architecture & Approach:** Map out affected modules in `src/` (`api/`, `agent/`, `tools/`, `rag/`, `core/`), graph nodes/edges, and infrastructure (`Dockerfile`, `docker-compose.yml`). Include a Mermaid diagram when the flow is non-trivial.
   - **Data Models & State Changes:** Define Pydantic models, `AgentState` fields (with reducers such as `operator.add`), `Settings` entries, and any data files or vector store changes.
   - **Interfaces & Endpoints:** Detail function signatures (with type hints), `@tool` names/descriptions/`args_schema`, FastAPI routes, SSE chunk formats, and request/response payloads.
   - **Security & Guardrails:** Explain how the change preserves the PII isolation, commercial secrecy and SSE rules from the constitution.
   - **Testing Strategy:** Specify `pytest` / `pytest-asyncio` tests (preferring `@pytest.mark.parametrize`), use of `MockGeminiLLM` and `unittest.mock` (no network), and end-to-end tests proving each Acceptance Criterion.
   - **Decisions & Out of Scope:** Record architectural decisions (table with justification) and deviations from `spec.md`.
3. **Generate `plan.md`:**
   - Write the finalized technical plan into `plan.md` in the active feature directory, in Portuguese.
4. **Human Review Gate:**
   - Ask the user to review the architectural choices and sign off before running `/tasks`.
