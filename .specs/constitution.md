# Project Constitution
**Repository:** [Project Name]
**Last Updated:** 2026-10-19

## 1. Tech Stack & Core Libraries
- **Language:** Go 1.22+
- **Routing:** standard `net/http` (no third-party frameworks unless specified)
- **Database:** PostgreSQL with `pgx` driver
- **Templating:** `html/template` / HTMX (if applicable)

## 2. Architectural Rules
- **Layered Architecture:** Strict separation between Handlers, Services, and Repositories.
- **Dependency Injection:** Services and Repositories must be instantiated via constructors and passed as dependencies. No global state.
- **Errors:** Always wrap errors with context using `fmt.Errorf("failed to do X: %w", err)`. Never discard errors.

## 3. Testing Mandates
- All core business logic in the Service layer must have unit tests.
- Use Table-Driven Tests for testing multiple inputs/outputs.
- Mocking should be done via interfaces, not monkey-patching.

## 4. Coding Style & Conventions
- **Early Returns:** Avoid deep nesting. Handle errors and return immediately.
- **Variable Naming:** Short and concise for local variables (e.g., `r` for request, `db` for database). Descriptive names for package-level variables and structs.
- **Concurrency:** Prefer channels and `select` over mutexes where appropriate, but document any complex goroutine lifecycles.
