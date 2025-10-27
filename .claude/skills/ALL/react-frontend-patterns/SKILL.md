---
name: react-frontend-patterns
description: Complete reference for React 18, TypeScript, Hooks, state management, testing
type: documentation
---

# React Frontend Patterns

## Overview

Production-grade React 18+ patterns with TypeScript strict mode. Covers functional components, custom hooks, state management with Context and Redux, comprehensive testing with Jest and React Testing Library.

## React 18+ Functional Components

### Basic Component Structure
```tsx
import React from 'react';

interface UserProps {
  id: number;
  name: string;
  onUpdate?: (name: string) => void;
}

export const UserCard: React.FC<UserProps> = ({ id, name, onUpdate }) => {
  return (
    <div className="user-card">
      <h2>{name}</h2>
      <p>ID: {id}</p>
      {onUpdate && (
        <button onClick={() => onUpdate(name)}>Update</button>
      )}
    </div>
  );
};
```

### Compound Components Pattern
```tsx
interface CompoundProps {
  children: React.ReactNode;
}

const Card: React.FC<CompoundProps> = ({ children }) => (
  <div className="card">{children}</div>
);

const CardHeader: React.FC<CompoundProps> = ({ children }) => (
  <div className="card-header">{children}</div>
);

const CardBody: React.FC<CompoundProps> = ({ children }) => (
  <div className="card-body">{children}</div>
);

Card.Header = CardHeader;
Card.Body = CardBody;

// Usage
<Card>
  <Card.Header>Title</Card.Header>
  <Card.Body>Content</Card.Body>
</Card>
```

### Higher-Order Component Pattern
```tsx
function withAuth<P extends object>(
  Component: React.ComponentType<P>
): React.FC<P> {
  return (props: P) => {
    const [isAuth, setIsAuth] = React.useState(false);

    React.useEffect(() => {
      // Check authentication
      checkAuth().then(setIsAuth);
    }, []);

    if (!isAuth) return <div>Not authorized</div>;
    return <Component {...props} />;
  };
}

const ProtectedComponent = withAuth(SomeComponent);
```

## TypeScript Strict Mode

### Type Definitions
```tsx
// Strict null checks
interface User {
  id: number;
  email: string | null;
  profile?: {
    avatar: string;
    bio: string;
  };
}

// Strict function types
type ApiHandler = (data: unknown) => Promise<void>;

// Generic constraints
interface Repository<T extends { id: number }> {
  get(id: number): Promise<T>;
  list(): Promise<T[]>;
}

class UserRepository implements Repository<User> {
  async get(id: number): Promise<User> {
    // Implementation
    return { id, email: "test@example.com" };
  }

  async list(): Promise<User[]> {
    return [{ id: 1, email: "test@example.com" }];
  }
}
```

### NoImplicitAny Prevention
```tsx
// Bad: any type
const handleClick = (event: any) => { };

// Good: proper typing
const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
  event.preventDefault();
};

// Generic handlers
function useAsync<T>(fn: () => Promise<T>) {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setLoading(true);
    fn().then(setData).finally(() => setLoading(false));
  }, [fn]);

  return { data, loading };
}
```

## Hooks Patterns

### useState + useCallback
```tsx
import { useState, useCallback } from 'react';

interface Counter {
  value: number;
}

export const Counter: React.FC = () => {
  const [count, setCount] = useState<Counter>({ value: 0 });

  const increment = useCallback(() => {
    setCount(prev => ({ value: prev.value + 1 }));
  }, []);

  const decrement = useCallback(() => {
    setCount(prev => ({ value: prev.value - 1 }));
  }, []);

  return (
    <div>
      <p>{count.value}</p>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
    </div>
  );
};
```

### useEffect Data Fetching
```tsx
import { useEffect, useState } from 'react';

export const UserList: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchUsers = async () => {
      try {
        const response = await fetch('/api/users');
        if (!response.ok) throw new Error('Failed to fetch');

        const data = await response.json();
        if (isMounted) {
          setUsers(data);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchUsers();
    return () => { isMounted = false; };
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <ul>
      {users.map(user => <li key={user.id}>{user.name}</li>)}
    </ul>
  );
};
```

### Custom Hooks
```tsx
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error storing value:', error);
    }
  };

  return [storedValue, setValue] as const;
}
```

## State Management

### Context API Pattern
```tsx
interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = React.useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
```

### Redux Pattern (with Redux Toolkit)
```tsx
import { createSlice, configureStore, PayloadAction } from '@reduxjs/toolkit';

interface UserState {
  current: User | null;
  loading: boolean;
  error: string | null;
}

const userSlice = createSlice({
  name: 'user',
  initialState: { current: null, loading: false, error: null } as UserState,
  reducers: {
    fetchUserStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchUserSuccess: (state, action: PayloadAction<User>) => {
      state.current = action.payload;
      state.loading = false;
    },
    fetchUserError: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },
  },
});

const store = configureStore({
  reducer: {
    user: userSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

## Jest + React Testing Library

### Component Tests
```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserCard } from './UserCard';

describe('UserCard', () => {
  it('renders user name', () => {
    render(<UserCard id={1} name="John" />);
    expect(screen.getByText('John')).toBeInTheDocument();
  });

  it('calls onUpdate when button clicked', async () => {
    const handleUpdate = jest.fn();
    render(<UserCard id={1} name="John" onUpdate={handleUpdate} />);

    await userEvent.click(screen.getByRole('button'));
    expect(handleUpdate).toHaveBeenCalledWith('John');
  });
});
```

### Hook Tests
```tsx
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

describe('useLocalStorage', () => {
  it('persists value to localStorage', () => {
    const { result } = renderHook(() => useLocalStorage('test', 'initial'));

    act(() => {
      result.current[1]('updated');
    });

    expect(result.current[0]).toBe('updated');
    expect(localStorage.getItem('test')).toBe('"updated"');
  });
});
```

### Integration Tests
```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { UserList } from './UserList';

it('fetches and displays users', async () => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve([{ id: 1, name: 'John' }]),
    })
  );

  render(<UserList />);

  await waitFor(() => {
    expect(screen.getByText('John')).toBeInTheDocument();
  });
});
```

## Integration Checklist

- [ ] React 18 with strict mode enabled
- [ ] TypeScript strict mode configured (tsconfig.json)
- [ ] All components typed with React.FC<Props>
- [ ] useState, useEffect, useCallback implemented correctly
- [ ] Custom hooks created for reusable logic
- [ ] Context API providers set up
- [ ] Redux store configured with slices
- [ ] Jest configured with proper test setup
- [ ] React Testing Library installed and configured
- [ ] Component unit tests written
- [ ] Hook tests using renderHook
- [ ] Integration tests with mocked API
- [ ] Code coverage target >80%
- [ ] ESLint/Prettier configured
