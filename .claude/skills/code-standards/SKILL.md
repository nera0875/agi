---
name: code-standards
description: Pattern standards code - naming, structure, best practices
---

Standards code qualité universels.

**Naming Conventions**:
- Variables: camelCase (isActive, userId)
- Functions: verbNoun (getUser, validateInput, handleSubmit)
- Classes: PascalCase (UserService, DataValidator)
- Files: kebab-case (user-service.js, auth-handler.py)
- Constants: UPPER_SNAKE_CASE (MAX_RETRIES, API_TIMEOUT)

**File Structure**:
- Organize by feature, not by type
- Max 200 lines per file (split if larger)
- Clear index/exports at directory level
- Related files close together

**Best Practices**:
- DRY: Don't repeat code (extract to functions)
- SOLID: Single responsibility, Open/closed
- Error handling: Explicit try/catch or error callbacks
- Comments: Explain "why", not "what"
- Tests: Co-locate with source code

**Code Review Checklist**:
- [ ] Tests pass, coverage >80%
- [ ] Naming clear and consistent
- [ ] No duplicated logic
- [ ] Error handling complete
- [ ] Public APIs documented
- [ ] No unused imports/variables
- [ ] Performance acceptable
