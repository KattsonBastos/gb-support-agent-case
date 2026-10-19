---
name: implement
description: Systematically execute tasks from tasks.md phase by phase, verifying each step
---

# /implement: Task Execution Workflow

## Objective
Autonomously and incrementally implement tasks defined in `tasks.md` while adhering to the constitution and active spec.

## Instructions
1. **Load Context:**
   - Read active `tasks.md`, `plan.md`, `spec.md`, and `.specs/constitution.md`.
2. **Identify Next Task:**
   - Find the first unchecked task `- [ ]` in the lowest incomplete phase.
   - Do NOT jump across phases or implement features out of order.
3. **Execute Task:**
   - Implement only the code and tests required for that specific task.
   - Strictly follow the patterns in `.specs/constitution.md`.
   - Run tests and linters to verify the change passes.
4. **Mark Completion:**
   - Update `tasks.md` to mark the task completed: `- [x] Task X.Y: ...`.
   - Summarize what was accomplished.
5. **Phase Gate:**
   - When all tasks in a phase are complete, pause and summarize the phase outcome before continuing to the next phase.
