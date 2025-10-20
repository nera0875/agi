---
name: graphql-debugging
category: quality
type: methodology
tags: [graphql, debugging, strawberry, apollo]
complexity: intermediate
---

# GraphQL Debugging Guide

Debugging GraphQL queries, mutations, subscriptions - backend & frontend.

## Backend (Strawberry/FastAPI)

### Schema Validation

```python
# Verify schema compiles
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class Query:
    @strawberry.field
    def get_memory(self, id: int) -> "Memory":
        """Query memory by ID"""
        return Memory(id=id, content="test")

@strawberry.type
class Memory:
    id: int
    content: str

# Test schema
schema = strawberry.Schema(query=Query)
print(schema.as_str())  # Print schema to verify
```

### Resolver Debugging

```python
# Enable query logging
@strawberry.type
class Query:
    @strawberry.field
    def get_memory(self, id: int) -> "Memory":
        print(f"[RESOLVER] get_memory called with id={id}")  # Debug log

        try:
            memory = db.query(Memory).filter_by(id=id).first()
            if not memory:
                print(f"[RESOLVER] Memory {id} not found")
                return None

            print(f"[RESOLVER] Returning memory: {memory.content}")
            return memory
        except Exception as e:
            print(f"[RESOLVER] Error: {e}")
            raise

# FastAPI route
app = FastAPI()
graphql_app = GraphQLRouter(schema, debug=True)  # Debug mode
app.include_router(graphql_app, prefix="/graphql")
```

### Query/Mutation Validation

```python
# Check query execution
query_str = """
query GetMemory($id: Int!) {
  getMemory(id: $id) {
    id
    content
  }
}
"""

variables = {"id": 1}

# Execute query
from strawberry import execute_sync

result = execute_sync(schema, query_str, variable_values=variables)

print(f"Data: {result.data}")
print(f"Errors: {result.errors}")  # Show errors if any
```

### Common Resolver Issues

#### Issue: Null Response

```python
# ❌ PROBLEM - Null response
@strawberry.field
def get_memory(self, id: int) -> Memory:  # Non-null return type
    memory = db.query(Memory).filter_by(id=id).first()
    return memory  # Could be None!

# Result: GraphQL error "Cannot return null for non-null field"

# ✅ FIX - Optional return
@strawberry.field
def get_memory(self, id: int) -> Optional[Memory]:
    memory = db.query(Memory).filter_by(id=id).first()
    return memory  # None is OK

# Or check in resolver
@strawberry.field
def get_memory(self, id: int) -> Memory:
    memory = db.query(Memory).filter_by(id=id).first()
    if not memory:
        raise ValueError(f"Memory {id} not found")  # Explicit error
    return memory
```

#### Issue: Type Mismatch

```python
# ❌ PROBLEM - Type mismatch
@strawberry.type
class Memory:
    id: int
    created_at: str  # String in schema

# But resolver returns:
created_at: datetime  # datetime object

# Result: Serialization error

# ✅ FIX - Convert in resolver
@strawberry.field
def get_memory(self, id: int) -> Memory:
    db_memory = db.query(DBMemory).filter_by(id=id).first()
    return Memory(
        id=db_memory.id,
        created_at=db_memory.created_at.isoformat()  # Convert to string
    )
```

#### Issue: Missing Field

```python
# ❌ PROBLEM - Query field not implemented
query = """
{
  getMemory(id: 1) {
    id
    content
    author { name }  # Not in schema!
  }
}
"""

# Result: GraphQL error "Cannot query field 'author'"

# ✅ FIX - Add to schema
@strawberry.type
class Memory:
    id: int
    content: str
    author: Optional["User"] = None  # Add missing field

@strawberry.field
def get_memory(self, id: int) -> Memory:
    db_memory = db.query(DBMemory).filter_by(id=id).first()
    author = db_memory.author if db_memory else None  # Load relation
    return Memory(id=db_memory.id, content=db_memory.content, author=author)
```

### Mutation Debugging

```python
# ✅ GOOD - Mutation with error handling
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_memory(self, content: str, type: str) -> MemoryResponse:
        try:
            # Validation
            if not content.strip():
                return MemoryResponse(success=False, error="Content empty")

            # Create
            memory = Memory(content=content, type=type)
            db.session.add(memory)
            db.session.commit()

            return MemoryResponse(success=True, memory=memory)
        except Exception as e:
            logger.error(f"Failed to create memory: {e}")
            return MemoryResponse(success=False, error=str(e))

@strawberry.type
class MemoryResponse:
    success: bool
    error: Optional[str] = None
    memory: Optional[Memory] = None
```

### Subscription Debugging

```python
# ✅ GOOD - Subscription with context
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def on_memory_created(self) -> AsyncGenerator[Memory, None]:
        """Stream new memories as created"""
        # Get queue from context
        context = strawberry.get_context()
        channel = context.get("memory_channel")

        if not channel:
            logger.warning("No memory channel in context")
            return

        async for memory in channel:
            logger.debug(f"Sending memory {memory.id}")
            yield memory
```

## Frontend (Apollo Client)

### Query Debugging

```typescript
// ✅ Enable Apollo DevTools
import { ApolloClient, InMemoryCache, HttpLink } from '@apollo/client';

const client = new ApolloClient({
  link: new HttpLink({
    uri: 'http://localhost:8000/graphql',
    credentials: 'include',
  }),
  cache: new InMemoryCache(),
  connectToDevTools: true,  // Enable DevTools
});

// DevTools now available at http://localhost:3000/__APOLLO_DEVTOOLS__
```

### useQuery Hook Issues

```typescript
// ❌ PROBLEM - Missing field in query
const GET_MEMORY = gql`
  query GetMemory($id: Int!) {
    getMemory(id: $id) {
      id
      content
      # author not requested!
    }
  }
`;

// Component tries to access
const { data } = useQuery(GET_MEMORY, { variables: { id: 1 } });
console.log(data.getMemory.author);  // undefined!

// ✅ FIX - Add to query
const GET_MEMORY = gql`
  query GetMemory($id: Int!) {
    getMemory(id: $id) {
      id
      content
      author {
        id
        name
      }
    }
  }
`;
```

### useMutation Hook Issues

```typescript
// ❌ PROBLEM - Variables type mismatch
const CREATE_MEMORY = gql`
  mutation CreateMemory($input: CreateMemoryInput!) {
    createMemory(input: $input) {
      id
      content
    }
  }
`;

const [mutate] = useMutation(CREATE_MEMORY);

// Call with wrong type
mutate({
  variables: {
    input: "just a string"  // Should be object!
  }
});

// ✅ FIX - Correct variable type
interface CreateMemoryInput {
  content: string;
  type: string;
}

mutate({
  variables: {
    input: { content: "test", type: "short_term" }
  }
});
```

### useSubscription Hook Issues

```typescript
// ❌ PROBLEM - Subscription not starting
const ON_MEMORY = gql`
  subscription OnMemory {
    onMemoryCreated {
      id
      content
    }
  }
`;

const { data, error } = useSubscription(ON_MEMORY);

// Subscription never receives data
// → Check: WebSocket connection
// → Check: Subscription implemented in backend
// → Check: Console for errors

// ✅ DEBUG - Check WebSocket
// Open DevTools → Network → WS tab
// Should see WebSocket connection to /graphql

// ✅ FIX - Add debugging
const { data, error, loading } = useSubscription(ON_MEMORY);

useEffect(() => {
  if (loading) console.log("Subscription loading...");
  if (error) console.error("Subscription error:", error);
  if (data) console.log("Received:", data);
}, [loading, error, data]);
```

### Apollo Cache Issues

```typescript
// ❌ PROBLEM - Stale cache after mutation
const CREATE_MEMORY = gql`
  mutation CreateMemory($input: CreateMemoryInput!) {
    createMemory(input: $input) {
      id
      content
    }
  }
`;

const GET_MEMORIES = gql`
  query GetMemories {
    memories {
      id
      content
    }
  }
`;

const [mutate] = useMutation(CREATE_MEMORY);

mutate({
  variables: { input: { content: "new" } }
});

// Cache not updated, query still shows old data

// ✅ FIX 1 - Refetch query
mutate({
  variables: { input: { content: "new" } },
  refetchQueries: [{ query: GET_MEMORIES }]  // Refetch after mutation
});

// ✅ FIX 2 - Update cache manually
mutate({
  variables: { input: { content: "new" } },
  update: (cache, { data }) => {
    const cached = cache.readQuery({ query: GET_MEMORIES });
    cache.writeQuery({
      query: GET_MEMORIES,
      data: {
        memories: [...cached.memories, data.createMemory]
      }
    });
  }
});
```

## Testing GraphQL

### Backend Testing

```python
import pytest
from strawberry import execute_sync

@pytest.fixture
def schema():
    from app.graphql import schema
    return schema

def test_get_memory_query(schema, db_memory):
    query = """
    query {
      getMemory(id: %d) {
        id
        content
      }
    }
    """ % db_memory.id

    result = execute_sync(schema, query)

    assert result.errors is None
    assert result.data["getMemory"]["id"] == db_memory.id
    assert result.data["getMemory"]["content"] == db_memory.content

def test_create_memory_mutation(schema):
    mutation = """
    mutation {
      createMemory(input: {content: "test", type: "short_term"}) {
        success
        memory {
          id
          content
        }
      }
    }
    """

    result = execute_sync(schema, mutation)

    assert result.errors is None
    assert result.data["createMemory"]["success"] is True
```

### Frontend Testing

```typescript
import { MockedProvider } from '@apollo/client/testing';
import { render, screen, waitFor } from '@testing-library/react';

describe('GetMemory Query', () => {
  it('should fetch and display memory', async () => {
    const mocks = [
      {
        request: {
          query: GET_MEMORY,
          variables: { id: 1 }
        },
        result: {
          data: {
            getMemory: {
              id: 1,
              content: 'Test memory'
            }
          }
        }
      }
    ];

    render(
      <MockedProvider mocks={mocks}>
        <MemoryComponent id={1} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Test memory')).toBeInTheDocument();
    });
  });
});
```

## Network Inspection

### GraphQL Requests

```bash
# Using curl to test queries
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ getMemory(id: 1) { id content } }"
  }' | jq .

# With variables
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($id: Int!) { getMemory(id: $id) { id content } }",
    "variables": { "id": 1 }
  }' | jq .
```

### Browser DevTools

```markdown
1. Open F12 → Network tab
2. Filter: XHR
3. Look for graphql requests
4. Click request → Response tab
5. Check:
   - Query/mutation name
   - Variables sent
   - Response data or errors
   - Response time
```

## Common GraphQL Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot query field X` | Field doesn't exist in schema | Add field to @strawberry.type |
| `Expected value to be...` | Type mismatch | Check variable types |
| `Cannot return null for non-null` | Resolver returns None | Use Optional[T] or raise error |
| `Field must not be nil` | Required argument missing | Add required args to query |
| `Unknown type` | Type not registered | Import and use in schema |
| `Permission denied` | Auth check failed | Verify token/permissions |
| `Query timeout` | DB query slow | Add index/optimize query |

## Debugging Checklist

```markdown
- [ ] Schema valid: `schema.as_str()` outputs correctly
- [ ] Query syntax valid: Try in GraphQL playground
- [ ] Field names exact match: Check case
- [ ] Variables match schema: Types correct
- [ ] Resolver implemented: Function exists
- [ ] Resolver returns data: Add logging
- [ ] No null pointer: Check Optional types
- [ ] Type conversions: datetime → string, etc.
- [ ] DB queries work: Test separately
- [ ] Permissions granted: User has access
- [ ] Cache cleared: If stale data
```
