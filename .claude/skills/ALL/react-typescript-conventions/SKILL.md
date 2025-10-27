---
name: react-typescript-conventions
description: React functional components, TypeScript strict mode, folder structure, hooks patterns, state management
---

**Pattern**: React 18 with TypeScript strict mode, functional components, custom hooks.

**Usage**: Building React components, managing state with hooks, organizing folders, type safety.

**Instructions**:
- Use functional components with `FC<Props>` type
- Enable TypeScript strict mode in `tsconfig.json`
- Define prop interfaces separate from components
- Use custom hooks for logic extraction
- Organize folders: `components/`, `hooks/`, `utils/`, `pages/`
- Use `useState`, `useEffect`, `useContext` for state
- Add ESLint + Prettier for formatting

**Component Pattern**:
```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
}

export const Button: React.FC<ButtonProps> = ({ label, onClick }) => (
  <button onClick={onClick}>{label}</button>
);
```

**Folder Structure**:
```
frontend/src/
├── components/  (reusable)
├── pages/       (route pages)
├── hooks/       (custom hooks)
└── utils/       (helpers)
```

**State Management**: Use Context API for simple state, Redux for complex.
