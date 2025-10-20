---
name: frontend-bug-checklist
category: quality
type: checklist
tags: [frontend, react, typescript, debugging, errors]
complexity: beginner
---

# Frontend Bug Checklist - React/TypeScript

Checklist rapide pour diagnostiquer bugs frontend.

## JavaScript Console Errors

```markdown
### When: Red errors in console (F12)

- [ ] **Read Error Message**
  - [ ] Full message visible: Expand if truncated
  - [ ] Stack trace present: Click to expand
  - [ ] File and line number: Click to open in Sources

- [ ] **Component Mount**
  - [ ] Component renders: Check React DevTools
  - [ ] Props passed correctly: Log props in component
  - [ ] State initialized: Check useState default values

- [ ] **Type Errors**
  - [ ] TypeScript compiled: Check for TS errors
  - [ ] Types defined correctly: Check interfaces
  - [ ] Null checks: `if (var !== null) ...`

- [ ] **Dependency Errors**
  - [ ] Library installed: `npm list package-name`
  - [ ] Import path correct: Check package.json
  - [ ] Version compatible: Check documentation
```

---

## Blank Screen / White Page

```markdown
### When: Nothing renders, just white page

- [ ] **Browser Console**
  - [ ] Open F12 → Console tab
  - [ ] Look for red errors
  - [ ] Check for warnings

- [ ] **React DevTools**
  - [ ] React DevTools extension installed
  - [ ] Root component visible: Inspect component tree
  - [ ] Any error boundary: Look for error indicator

- [ ] **Build Status**
  - [ ] Development server running: Check terminal
  - [ ] No compile errors: Read build output
  - [ ] Files changed detected: Automatic reload

- [ ] **Index Entry Point**
  - [ ] `src/main.tsx` exists: Check file
  - [ ] Root div `id="root"` in `index.html`
  - [ ] React.render called: `ReactDOM.createRoot(...).render(...)`

- [ ] **Styling**
  - [ ] Tailwind built: Check dist/output.css
  - [ ] CSS not hiding everything: Inspect body/html

- [ ] **External Resources**
  - [ ] No 404 on JS files: Check Network tab
  - [ ] API endpoints reachable: Check Network XHR
```

---

## Infinite Loops / App Freezes

```markdown
### When: Tab hangs, CPU at 100%, no response

- [ ] **useEffect Dependencies**
  - [ ] Check all useEffect hooks: `useEffect(() => {...}, [deps])`
  - [ ] Missing dependencies: Add all referenced variables
  - [ ] Circular dependencies: e.g., `useEffect(() => setState, [state])`

- [ ] **Event Handlers**
  - [ ] No infinite onClick loops: Check click handlers
  - [ ] setInterval not duplicated: Only one per component
  - [ ] setTimeout canceled: `useEffect(() => { const id = setTimeout(...); return () => clearTimeout(id) })`

- [ ] **API Calls**
  - [ ] Data fetching in useEffect: Not in render
  - [ ] Fetch not in render: Would loop infinitely

- [ ] **Logic Loops**
  - [ ] Recursive function base case: Check termination
  - [ ] While loops: Have break condition
  - [ ] For loops: Counter increments: `for (let i = 0; i < n; i++)`

- [ ] **Network Tab Check**
  - [ ] Open DevTools → Network
  - [ ] Repeated API calls: Same request many times?
  - [ ] Waterfall view: Shows request chains
```

---

## Network / GraphQL Errors

```markdown
### When: "Network Error", GraphQL query fails, 404/500

- [ ] **Network Tab**
  - [ ] Open F12 → Network tab
  - [ ] Filter: XHR (XmlHttpRequest)
  - [ ] Look for failed requests (red)
  - [ ] Click to see details

- [ ] **GraphQL Query**
  - [ ] Query syntax valid: Try in GraphQL playground
  - [ ] Field names match schema: Exact case
  - [ ] Variables correct type: Match schema
  - [ ] Authorization header: If required

- [ ] **API Endpoint**
  - [ ] Backend running: Check terminal
  - [ ] Endpoint exists: Check backend routes
  - [ ] URL correct in frontend: Check API_URL env var
  - [ ] Port correct: Check localhost:8000 vs 3000

- [ ] **CORS Issues**
  - [ ] Error mentions CORS: "Access-Control-Allow-Origin"
  - [ ] Backend CORS configured: Check FastAPI setup
  - [ ] Credentials sent: Check `credentials: 'include'`

- [ ] **Authentication**
  - [ ] Token in localStorage: Check DevTools Storage
  - [ ] Token not expired: Check expiry
  - [ ] Header sent: Check request headers "Authorization: Bearer ..."

- [ ] **Response Data**
  - [ ] Response status: Should be 200-299
  - [ ] Response body: Not empty
  - [ ] Data format: Valid JSON
```

---

## State Management Issues

```markdown
### When: Component doesn't update, data stale, state lost

- [ ] **useState Hooks**
  - [ ] Initial value set: `useState(initialValue)`
  - [ ] setState called correctly: `setState(newValue)` not `setState(currentState + 1)` in event
  - [ ] Key prop on lists: `<div key={id}>` for lists

- [ ] **Effect Dependencies**
  - [ ] useEffect dependencies correct: `useEffect(() => {...}, [dep1, dep2])`
  - [ ] Missing deps: Add all variables used in effect
  - [ ] Extra deps: Remove if not needed (performance)

- [ ] **Component Re-renders**
  - [ ] Parent not re-rendering: Check parent state
  - [ ] Props not changing: Log props in useEffect
  - [ ] Memoization working: Check React.memo() if used

- [ ] **Context API (if used)**
  - [ ] Provider wraps component: Check JSX tree
  - [ ] useContext hook used: `const value = useContext(MyContext)`
  - [ ] Value updates: Check context provider value changes

- [ ] **Apollo Client (if used)**
  - [ ] useQuery hook: `const { data, loading, error } = useQuery(QUERY)`
  - [ ] Cache updating: After mutation, check refetchQueries
  - [ ] Stale cache: Force refresh if needed
```

---

## React Hooks Errors

```markdown
### When: "Hooks called outside", "Invalid hook call"

- [ ] **Hook Location**
  - [ ] Hook at top level: Not inside if/for/function
  - [ ] Only in components/custom hooks: Not in regular functions
  - [ ] Same order: Hooks always called same order

- [ ] **useEffect Cleanup**
  - [ ] Return cleanup function: `return () => { cleanup }`
  - [ ] EventListener removed: In cleanup
  - [ ] Subscription canceled: In cleanup
  - [ ] Timer cleared: `clearTimeout()` in cleanup

- [ ] **useMemo/useCallback**
  - [ ] Dependencies array provided: `useMemo(() => {...}, [deps])`
  - [ ] Return type matches: No return in function

- [ ] **useRef**
  - [ ] Not re-render trigger: Mutate .current directly
  - [ ] Null initially: Set in useEffect
  - [ ] Check before use: `if (ref.current) ...`

- [ ] **Custom Hooks**
  - [ ] Hook name starts with "use": `useCustomHook`
  - [ ] Rules of Hooks followed: Top level only
  - [ ] Return type documented: For TypeScript
```

---

## Apollo Client Issues

```markdown
### When: GraphQL subscription fails, cache issues, no data

- [ ] **Query Hook**
  - [ ] useQuery imported: `import { useQuery } from '@apollo/client/react'`
  - [ ] Query passed: `useQuery(GET_MEMORY_QUERY)`
  - [ ] Data destructured: `const { data, loading, error } = useQuery(...)`

- [ ] **Mutation Hook**
  - [ ] useMutation imported
  - [ ] Mutation defined: `const [mutate, { loading, error }] = useMutation(...)`
  - [ ] Call function: `mutate({ variables: { input } })`
  - [ ] Handle response: `.then(result => ...)`

- [ ] **Subscription Hook**
  - [ ] useSubscription imported: `import { useSubscription } from '@apollo/client/react'`
  - [ ] Subscription defined correctly
  - [ ] No loading: Subscriptions don't use loading like queries

- [ ] **Apollo Cache**
  - [ ] Cache key correct: `__typename` and `id` present
  - [ ] Refetch after mutation: Add `refetchQueries`
  - [ ] Update cache manually: `cache.modify()` if needed

- [ ] **Network Configuration**
  - [ ] Apollo Client configured: `new ApolloClient({ ... })`
  - [ ] Link correct: HttpLink or WsLink for subscriptions
  - [ ] Headers included: Authorization token
```

---

## TypeScript Errors

```markdown
### When: "TS error", red squiggles, build fails

- [ ] **Type Definitions**
  - [ ] Type imported/defined: Check interface
  - [ ] Interface matches data: All fields present
  - [ ] Optional fields: Use `?` for optional

- [ ] **Null/Undefined Safety**
  - [ ] Null check: `if (variable !== null) ...`
  - [ ] Optional chaining: `obj?.prop?.nested`
  - [ ] Non-null assertion: `variable!` (use sparingly)

- [ ] **Function Types**
  - [ ] Parameter types: `function(param: Type)`
  - [ ] Return type: `function(): ReturnType`
  - [ ] Async functions: Returns Promise

- [ ] **Generic Types**
  - [ ] Generic parameter specified: `<T>` used correctly
  - [ ] Props typed: `interface Props { ... }`
  - [ ] Children typed: `children?: React.ReactNode`

- [ ] **Build Check**
  - [ ] Run type check: `npm run build` or `tsc --noEmit`
  - [ ] Fix all errors before deploying
```

---

## Component Lifecycle Issues

```markdown
### When: Component doesn't mount/unmount correctly, memory leak

- [ ] **Mount Lifecycle**
  - [ ] Component renders: Check DOM
  - [ ] useEffect runs: Add console.log
  - [ ] Dependencies empty: `useEffect(() => {...}, [])` for mount

- [ ] **Unmount Lifecycle**
  - [ ] Cleanup function: `return () => { cleanup }`
  - [ ] Remove listeners: `element.removeEventListener()`
  - [ ] Cancel requests: `abortController.abort()`
  - [ ] Clear timers: `clearInterval()`, `clearTimeout()`

- [ ] **Component Reuse**
  - [ ] Key prop on lists: `<Component key={id} />`
  - [ ] Different key resets state: Intentional unmount/remount
  - [ ] Same key preserves state: If intended

- [ ] **Conditional Rendering**
  - [ ] Component exists in DOM: Check React DevTools
  - [ ] Props updated when condition changes: Check props
```

---

## Performance Issues

```markdown
### When: App slow, laggy, inefficient rendering

- [ ] **React DevTools Profiler**
  - [ ] Open DevTools → Profiler tab
  - [ ] Record interactions: Click record, interact, stop
  - [ ] Check render times: Identify slow components
  - [ ] Check flamegraph: See which components render

- [ ] **Unnecessary Re-renders**
  - [ ] Component memoized: `React.memo(Component)` if parent re-renders
  - [ ] Props stable: Don't create new objects in render
  - [ ] Keys correct: For lists, use stable keys

- [ ] **Large Lists**
  - [ ] Use virtualization: react-window or similar
  - [ ] Pagination: Load 50 at a time, not 10,000
  - [ ] Lazy loading: Load as user scrolls

- [ ] **Heavy Computations**
  - [ ] useMemo for expensive: `useMemo(() => expensiveCalc(), [deps])`
  - [ ] useCallback for functions: `useCallback(() => {...}, [deps])`
  - [ ] Move computation out of render

- [ ] **Bundle Size**
  - [ ] Check: `npm run build` and check dist/
  - [ ] Analyze: Use `webpack-bundle-analyzer`
  - [ ] Code split: Lazy load routes with React.lazy()
```

---

## CSS / Styling Issues

```markdown
### When: Styles not applied, layout broken, responsive issues

- [ ] **Tailwind Classes**
  - [ ] Classes spelled correctly: Exact case
  - [ ] Class applied: Check DevTools Inspector
  - [ ] Tailwind compiled: Check dist/output.css has class
  - [ ] Responsive: Check `sm:`, `md:`, `lg:` prefixes

- [ ] **CSS Specificity**
  - [ ] Tailwind !important: Classes have priority
  - [ ] Inline styles override: Check style attribute
  - [ ] Order matters: Last rule wins if equal specificity

- [ ] **Media Queries**
  - [ ] Mobile view: Resize browser or use DevTools
  - [ ] Breakpoints: sm (640px), md (768px), lg (1024px)
  - [ ] Touch events: Check on mobile device

- [ ] **Component Library (shadcn/ui)**
  - [ ] Component imported: `import { Button } from '@/components/ui/button'`
  - [ ] Props correct: Check component documentation
  - [ ] No duplicate: Already exists in shadcn/ui
```

---

## Error Boundary Pattern

### Use Error Boundaries to Catch React Errors

```typescript
import React from 'react';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div>Something went wrong: {this.state.error?.message}</div>;
    }

    return this.props.children;
  }
}

// Usage
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>
```

---

## Checklist Before Deployment

```markdown
- [ ] No console errors: F12 Console empty
- [ ] No console warnings: (or justified)
- [ ] TypeScript strict: `npm run build` passes
- [ ] Production env vars: Check VITE_API_URL
- [ ] API endpoints correct: No localhost:8000 in prod
- [ ] No hardcoded auth tokens: Use env vars
- [ ] Performance acceptable: Load time < 3s
- [ ] Mobile responsive: Works on phone
- [ ] All links work: No 404s
- [ ] Accessibility OK: ARIA labels present
```
