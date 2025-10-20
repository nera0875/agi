---
name: TypeScript Excellence
description: TypeScript strict mode, interfaces, type safety, and React/Apollo patterns
category: languages
language: typescript
version: 1.0
---

## TypeScript Strict Mode

All TypeScript files must use strict mode:

```typescript
// ✅ CORRECT
interface MemoryItem {
  id: string;
  content: string;
  createdAt: Date;
}

function getMemory(id: string): MemoryItem | null {
  // Implementation with full type safety
}

// ❌ WRONG
function getMemory(id: any): any {
  return null;
}
```

## Interfaces vs Types

Use **interfaces for object shapes**, types for unions/primitives:

```typescript
// ✅ CORRECT - Object contract
interface Memory {
  id: string;
  content: string;
  tags: string[];
}

// ✅ CORRECT - Union or primitive
type MemoryStatus = "active" | "archived" | "deleted";
type Result<T> = { success: true; data: T } | { success: false; error: string };

// ❌ WRONG - Type for object
type Memory = {
  id: string;
  content: string;
};
```

## Type Annotations

Always annotate function signatures and complex variables:

```typescript
// ✅ CORRECT
interface QueryOptions {
  limit: number;
  offset: number;
  sort: "asc" | "desc";
}

async function queryMemories(options: QueryOptions): Promise<Memory[]> {
  const result: Map<string, Memory> = new Map();
  return Array.from(result.values());
}

// ❌ WRONG
async function queryMemories(options) {
  const result = new Map();
  return Array.from(result.values());
}
```

## React Component Typing

Type all props and returns:

```typescript
// ✅ CORRECT
interface MemoryCardProps {
  memory: Memory;
  onDelete: (id: string) => void;
  isSelected?: boolean;
}

const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  onDelete,
  isSelected = false
}) => {
  return (
    <div className={isSelected ? "selected" : ""}>
      {memory.content}
    </div>
  );
};

// ❌ WRONG
const MemoryCard = ({ memory, onDelete }) => {
  return <div>{memory.content}</div>;
};
```

## Apollo Client Hooks

Type Apollo hooks with interfaces:

```typescript
// ✅ CORRECT
interface GetMemoriesData {
  memories: Memory[];
}

interface GetMemoriesVars {
  limit: number;
}

const { data, loading, error } = useQuery<GetMemoriesData, GetMemoriesVars>(
  GET_MEMORIES_QUERY,
  { variables: { limit: 10 } }
);

// ✅ GraphQL Subscriptions
interface OnMemoryUpdated {
  onMemoryUpdated: Memory;
}

useSubscription<OnMemoryUpdated>(MEMORY_SUBSCRIPTION);

// ❌ WRONG
const { data, loading, error } = useQuery(GET_MEMORIES_QUERY);
```

## shadcn/ui Components

Use only shadcn/ui components, never create custom UI:

```typescript
// ✅ CORRECT - Use shadcn/ui
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function MemoryCard() {
  return (
    <Card>
      <CardHeader>Title</CardHeader>
      <CardContent>
        <Button onClick={handleClick}>Action</Button>
      </CardContent>
    </Card>
  );
}

// ❌ WRONG - Don't create custom components
export function CustomButton() {
  return <button style={{...}}>Custom</button>;
}
```

## Error Boundaries

Always use error boundaries for component safety:

```typescript
// ✅ CORRECT
interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return <div>Error occurred</div>;
    }
    return this.props.children;
  }
}
```

## Accessibility (ARIA)

Always add ARIA labels:

```typescript
// ✅ CORRECT
<button
  onClick={handleDelete}
  aria-label="Delete memory item"
  title="Delete this memory"
>
  Delete
</button>

<div
  role="region"
  aria-live="polite"
  aria-label="Memory list"
>
  {memories.map(m => <MemoryCard key={m.id} memory={m} />)}
</div>

// ❌ WRONG
<button onClick={handleDelete}>X</button>
```

## Import Organization

```typescript
// ✅ CORRECT
// React/Framework
import React, { FC, useState } from "react";
import { useQuery, useMutation } from "@apollo/client/react";

// shadcn/ui
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

// Project components
import { MemoryCard } from "@/components/memory-card";
import { useMemoryStore } from "@/hooks/use-memory-store";

// Utils
import { formatDate } from "@/lib/utils";
```

## Naming Conventions

- **Files**: `kebab-case` (memory-card.tsx, use-memory.ts)
- **Components**: `PascalCase` (MemoryCard, MemoryList)
- **Functions/Hooks**: `camelCase` or `useXxx` for hooks (fetchMemories, useMemory)
- **Interfaces**: `PascalCase` ending with "Props" or specific suffix (MemoryCardProps)
- **Types**: `PascalCase` (Memory, MemoryStatus)

## Project Structure

```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui components (don't touch)
│   ├── memory-card.tsx
│   └── memory-list.tsx
├── pages/
│   ├── dashboard.tsx
│   └── memory-browser.tsx
├── hooks/
│   ├── use-memory.ts
│   └── use-memory-store.ts
├── lib/
│   └── utils.ts
├── types/
│   └── index.ts
└── App.tsx
```

## Generic Types

Use generics for reusable components:

```typescript
// ✅ CORRECT
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  onSelect: (item: T) => void;
}

function List<T extends { id: string }>({
  items,
  renderItem,
  onSelect
}: ListProps<T>) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id} onClick={() => onSelect(item)}>
          {renderItem(item)}
        </li>
      ))}
    </ul>
  );
}
```

## Key Rules Summary

- ✅ Strict mode always
- ✅ Interfaces for object contracts
- ✅ Full type annotations on functions
- ✅ Type all props (React.FC<Props>)
- ✅ Use only shadcn/ui components
- ✅ Error boundaries for safety
- ✅ ARIA labels for accessibility
- ✅ Generic types for reusability
- ✅ kebab-case for files, PascalCase for components
