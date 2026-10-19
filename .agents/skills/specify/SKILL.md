---
name: specify
description: Elicit requirements and structure the active feature spec.md adhering to SDD standards
---

# /specify: Feature Specification Workflow

## Objective
Guide the user through clarifying requirements, edge cases, and constraints to generate or update `spec.md` in the active feature directory.

## Instructions
1. **Load Context:**
   - Read `.specs/constitution.md` to understand tech stack, architecture, and coding rules.
   - Identify the active feature directory (from `.ksdd.yaml` or `.antigravity/sdd.md`). Feature directories follow `.specs/RFC-XXX-<feature-name>/`.
   - If no active spec exists, ask the user to run `ksdd new <feature-name> --id <id>` or specify one.
2. **Clarify Requirements:**
   - Ask 2–4 targeted clarifying questions regarding:
     - The core user/business problem being solved.
     - Definite Acceptance Criteria (testable outcomes).
     - Explicit Out-of-Scope boundaries (to prevent scope creep).
     - Edge cases, error handling, rate limits, or performance constraints.
3. **Generate `spec.md`:**
   - Fill in all sections of `spec.md`: Problem Statement, Acceptance Criteria (`- [ ] AC-1: ...`), Out of Scope, and Edge Cases.
   - Ensure requirements are functional and technology-agnostic (the technical details belong in `plan.md`).
4. **Human Review Gate:**
   - Present the drafted `spec.md` to the user and request confirmation before moving to the `/plan` phase.
