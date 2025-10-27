---
name: frontend-testing-patterns
description: Jest setup, React Testing Library patterns, component unit tests, E2E testing with Cypress/Playwright
---

**Pattern**: Jest + React Testing Library for unit tests, Cypress for E2E tests.

**Usage**: Writing component tests, integration tests, E2E tests, test coverage.

**Instructions**:
- Use Jest as test runner with React preset
- Use React Testing Library for component testing
- Test user behavior, not implementation (no enzyme)
- Use `@testing-library/react` and `@testing-library/jest-dom`
- Set up E2E tests with Cypress or Playwright
- Aim for >80% coverage on components

**Jest Config**:
```javascript
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"]
};
```

**Component Test Pattern**:
```typescript
import { render, screen } from "@testing-library/react";
import { Button } from "./Button";

test("renders button with label", () => {
  render(<Button label="Click me" onClick={() => {}} />);
  expect(screen.getByText("Click me")).toBeInTheDocument();
});
```

**E2E Pattern** (Cypress):
```javascript
cy.visit("/");
cy.get("[data-testid=login-btn]").click();
cy.url().should("include", "/dashboard");
```
