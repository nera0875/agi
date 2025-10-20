---
name: React Mastery
description: React hooks, components, and patterns for frontend agents
---

# React Mastery

Expertise React 18.3.1 pour agents frontend. Guide complet hooks, components, composition, patterns.

## Hooks Best Practices

### Data Fetching avec GraphQL Apollo
```tsx
import { useQuery } from '@apollo/client/react'
import { GET_DATA } from '@/graphql/queries'

const { data, loading, error } = useQuery(GET_DATA)

if (loading) return <Skeleton />
if (error) return <Alert variant="destructive">{error.message}</Alert>
return <div>{data}</div>
```

**Règles:**
- Importer depuis `@apollo/client/react` (hooks)
- Gérer 3 states: loading, error, data
- Toujours afficher Skeleton pendant chargement
- Display Alert pour erreurs

### Forms avec react-hook-form
```tsx
import { useForm } from 'react-hook-form'
import { Form, FormField, FormItem } from '@/components/ui/form'

const form = useForm({
  defaultValues: { /* ... */ }
})

const onSubmit = async (data) => {
  // Validation + submission
}

return (
  <Form {...form}>
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <FormField
        control={form.control}
        name="fieldName"
        render={({ field }) => <FormItem>{/* ... */}</FormItem>}
      />
    </form>
  </Form>
)
```

**Règles:**
- Validation via react-hook-form
- shadcn/ui Form components
- Type-safe avec TypeScript

### Custom Hooks Pattern
```tsx
export function useCustomLogic(param: string) {
  const [state, setState] = useState(null)

  useEffect(() => {
    // Logic
  }, [param])

  return { state, setState }
}
```

**Placement:** `frontend/src/hooks/use-feature.ts`

## Component Composition

### Structure Standard
```tsx
interface ComponentNameProps {
  variant?: 'default' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  className?: string
  // Props typées
}

export function ComponentName({
  variant = 'default',
  size = 'md',
  disabled = false,
  className,
}: ComponentNameProps) {
  // Hooks en haut
  const [state, setState] = useState(null)

  // Handlers
  const handleClick = () => {
    // Logic
  }

  // Render avec shadcn/ui
  return (
    <div className={cn('base-classes', className)}>
      {/* JSX */}
    </div>
  )
}
```

**Règles:**
- Props toujours typées (interface)
- Valeurs par défaut explicites
- Hooks au début
- Handlers nommés `handle*`
- Utiliser `cn()` pour classes

### shadcn/ui Components ONLY
Ne JAMAIS créer custom UI components. shadcn/ui fournit:
- Button, Card, Dialog, Form, Input, Label
- Select, Checkbox, Switch, Tabs, Accordion
- Toast, Alert, Skeleton, Badge, Avatar
- Popover, Sheet, Dropdown Menu, Command
- Table, Slider, Textarea, Separator

**Si composant manque:**
```bash
cd frontend
npx shadcn@latest add [component-name]
```

### Layout & Container Patterns
```tsx
// Page layout
export default function Page() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <Content />
      </main>
      <Footer />
    </div>
  )
}

// Card layout
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function CardLayout() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        Content here
      </CardContent>
    </Card>
  )
}
```

## State Management

### React State (useState)
**Usage:** Local component state, form values, UI toggles

```tsx
const [isOpen, setIsOpen] = useState(false)
const [count, setCount] = useState(0)
```

### Apollo Client Cache
**Usage:** Server state, GraphQL queries, caching

```tsx
const { data } = useQuery(GET_DATA)
// Apollo auto-manages cache

// Manual cache update:
cache.writeQuery({
  query: GET_DATA,
  data: { /* ... */ }
})
```

**Règles:**
- GraphQL data = Apollo cache (source vérité)
- Local state = useState
- Pas de Redux/Zustand (overhead)
- Apollo pour persistance

### TanStack Table State
**Usage:** Table state (sorting, filtering, pagination)

```tsx
import { useReactTable, getCoreRowModel } from '@tanstack/react-table'

const table = useReactTable({
  data,
  columns,
  getCoreRowModel: getCoreRowModel(),
  state: {
    sorting,
    columnFilters,
    rowSelection,
  },
  onSortingChange: setSorting,
  onColumnFiltersChange: setColumnFilters,
  onRowSelectionChange: setRowSelection,
})
```

**Features:**
- Sorting (multi-column)
- Filtering
- Row selection
- Column resizing
- Pagination
- Virtualization (@tanstack/react-virtual)

## Performance Optimization

### Memoization Patterns
```tsx
// Memo for expensive components
export const MemoComponent = memo(function Component({ data }) {
  return <div>{data}</div>
})

// useCallback for stable handlers
const handleSubmit = useCallback((value: string) => {
  // Logic
}, [dependency])

// useMemo for expensive computations
const processedData = useMemo(() => {
  return data.filter(/* ... */).map(/* ... */)
}, [data])
```

**Rules:**
- Memo si component re-renders souvent
- useCallback pour props handlers
- useMemo pour computations lourdes
- Measure avant optimiser (React DevTools Profiler)

### Lazy Loading & Code Splitting
```tsx
import { lazy, Suspense } from 'react'

const HeavyComponent = lazy(() => import('./HeavyComponent'))

export function App() {
  return (
    <Suspense fallback={<Skeleton />}>
      <HeavyComponent />
    </Suspense>
  )
}
```

### Virtualization (Large Lists)
```tsx
import { useVirtualizer } from '@tanstack/react-virtual'

export function VirtualList({ items }: { items: any[] }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,
  })

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      {virtualizer.getVirtualItems().map((virtualItem) => (
        <div key={virtualItem.key}>
          {items[virtualItem.index]}
        </div>
      ))}
    </div>
  )
}
```

## Styling Best Practices

### Tailwind CSS ONLY
- ✅ Utility-first classes
- ✅ Predefined colors, spacing, sizing
- ❌ Inline font-size/weight (use globals.css)
- ❌ Custom CSS (modify .css files, not inline)

```tsx
// Good
<div className="flex gap-4 items-center">
  <Button variant="primary" size="lg" />
</div>

// Bad
<div style={{ display: 'flex', fontSize: '14px' }}>
  <button style={{ fontWeight: 'bold' }}>Click</button>
</div>
```

### Class Name Merging
```tsx
import { cn } from '@/lib/utils'

function Button({ className, variant, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'px-4 py-2 rounded-lg font-medium',
        variant === 'primary' && 'bg-blue-600 text-white',
        variant === 'secondary' && 'bg-gray-200 text-gray-900',
        className // Override
      )}
      {...props}
    />
  )
}
```

### Responsive Design
```tsx
// Tailwind responsive prefixes
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Mobile: full width, Tablet: 1/2, Desktop: 1/3 */}
</div>

<button className="text-sm md:text-base lg:text-lg">
  {/* Responsive typography */}
</button>
```

## Accessibility (WCAG 2.1 AA)

### ARIA Attributes
```tsx
<button
  aria-label="Close dialog"
  aria-expanded={isOpen}
  aria-describedby="dialog-description"
>
  Close
</button>

<div id="dialog-description">
  This is the dialog content
</div>
```

### Semantic HTML
```tsx
// Good
<nav>...</nav>
<main>...</main>
<article>...</article>
<button>Click me</button> // Interactive elements

// Bad
<div role="button">Click me</div> // Use button element
<div>Navigation</div> // Should be nav
```

### Keyboard Navigation
```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  {/* Built-in: Esc closes, Tab cycles */}
</Dialog>

<button onKeyDown={(e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    handleAction()
  }
}}>
  Click or press Enter/Space
</button>
```

## Error Handling & Validation

### Error Boundaries
```tsx
import { useState } from 'react'

export function ErrorBoundary({ children }: { children: React.ReactNode }) {
  const [error, setError] = useState<Error | null>(null)

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    )
  }

  try {
    return <>{children}</>
  } catch (err) {
    setError(err as Error)
    return null
  }
}
```

### GraphQL Error Handling
```tsx
const { data, error } = useQuery(GET_DATA)

if (error) {
  return (
    <Alert variant="destructive">
      <AlertTitle>Query Failed</AlertTitle>
      <AlertDescription>
        {error.graphQLErrors?.[0]?.message || error.message}
      </AlertDescription>
    </Alert>
  )
}
```

### Form Validation
```tsx
const form = useForm({
  resolver: zodResolver(schema),
})

// Auto validation on blur/change
return (
  <FormField
    control={form.control}
    name="email"
    render={({ field, fieldState }) => (
      <FormItem>
        <Input {...field} />
        {fieldState.error && (
          <FormMessage>{fieldState.error.message}</FormMessage>
        )}
      </FormItem>
    )}
  />
)
```

## File Organization

```
frontend/src/
├── components/
│   ├── ui/                 (shadcn/ui - NE PAS MODIFIER)
│   ├── database/           (Feature-specific: DB explorer)
│   ├── brain/              (Feature-specific: Brain)
│   ├── layout/             (Shared: Header, Footer, Sidebar)
│   └── [feature]/          (Feature components)
├── hooks/
│   ├── use-query.ts        (GraphQL hooks)
│   ├── use-table.ts        (Table state)
│   └── use-[feature].ts    (Custom logic)
├── lib/
│   ├── utils.ts            (cn(), formatters)
│   └── api.ts              (HTTP utilities)
├── config/
│   └── api.ts              (API endpoints)
├── graphql/
│   ├── queries/            (GET queries)
│   ├── mutations/          (POST/PUT/DELETE)
│   └── subscriptions/      (Real-time)
├── types/
│   ├── api.ts              (API types)
│   └── domain.ts           (Business types)
├── pages/
│   ├── dashboard.tsx       (Pages)
│   └── [slug].tsx
└── guidelines/
    └── figma.md            (Design rules - LIRE EN PREMIER)
```

## Common Patterns

### Loading States
```tsx
if (loading) return <Skeleton className="h-96" />
if (error) return <ErrorAlert error={error} />
return <Content data={data} />
```

### Empty States
```tsx
if (!data?.items?.length) {
  return (
    <div className="text-center py-12">
      <Database className="mx-auto h-12 w-12 text-gray-400" />
      <h3 className="mt-2 text-sm font-medium text-gray-900">
        No items yet
      </h3>
    </div>
  )
}
```

### Confirmation Dialogs
```tsx
const [open, setOpen] = useState(false)

return (
  <>
    <Button onClick={() => setOpen(true)}>Delete</Button>
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogContent>
        <AlertDialogTitle>Are you sure?</AlertDialogTitle>
        <AlertDialogAction onClick={handleDelete}>
          Delete
        </AlertDialogAction>
      </AlertDialogContent>
    </AlertDialog>
  </>
)
```

### Toast Notifications
```tsx
import { toast } from 'sonner'

toast.success('Operation successful')
toast.error('Something went wrong')
toast.promise(promise, {
  loading: 'Loading...',
  success: 'Success!',
  error: 'Error occurred',
})
```

## TypeScript Best Practices

### Strict Props Typing
```tsx
interface DataTableProps {
  data: Row[]
  columns: ColumnDef<Row>[]
  onRowClick?: (row: Row) => void
  isLoading?: boolean
  pageSize?: number
}

export function DataTable({
  data,
  columns,
  onRowClick,
  isLoading = false,
  pageSize = 10,
}: DataTableProps) {
  // ...
}
```

### Type-safe Event Handlers
```tsx
const handleChange: ChangeEventHandler<HTMLInputElement> = (e) => {
  const value = e.currentTarget.value
  // value is typed as string
}

const handleSubmit: FormEventHandler<HTMLFormElement> = (e) => {
  e.preventDefault()
  // ...
}
```

### Generic Components
```tsx
interface GenericCardProps<T> {
  data: T
  renderContent: (item: T) => React.ReactNode
  onSelect?: (item: T) => void
}

export function GenericCard<T>({
  data,
  renderContent,
  onSelect,
}: GenericCardProps<T>) {
  return (
    <Card onClick={() => onSelect?.(data)}>
      {renderContent(data)}
    </Card>
  )
}
```

## Critical Rules Summary

✅ **DO:**
- TypeScript strict mode
- shadcn/ui for all UI
- Tailwind utility classes
- React hooks pattern
- GraphQL Apollo Client
- WCAG 2.1 AA accessibility
- Responsive design
- Error boundaries

❌ **DON'T:**
- Custom UI components (shadcn exists)
- Framer Motion (use motion/react)
- react-resizable (use re-resizable)
- Inline font-size/weight
- Placeholder comments
- Modify tailwind.config.js
- Create CSS files (use Tailwind only)
- Non-semantic HTML

---

**Version:** 2025-10-19 v1 - React Mastery Skill
**Extracted from:** frontend.md agent guidelines
**Target:** Frontend agents React expertise
