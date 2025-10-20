---
name: API Documentation
description: OpenAPI specs, endpoint extraction, and curl examples generation
category: documentation
---

# API Documentation

Expertise in documenting REST and GraphQL APIs, extracting endpoints, and generating executable examples.

## REST API Documentation Structure

### Endpoint Template

```markdown
## GET /api/v1/memories

Retrieve memories with optional filtering.

**Authentication:** Bearer token (header)

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | int | No | Max results (default: 10) |
| offset | int | No | Pagination offset (default: 0) |
| query | string | No | Search memories by content |

**Response (200 OK):**
\`\`\`json
{
  "data": [
    {
      "id": 1,
      "content": "Memory content here",
      "created_at": "2025-10-19T10:30:00Z",
      "embedding": [0.1, 0.2, ...]
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 42
  }
}
\`\`\`

**Error (400 Bad Request):**
\`\`\`json
{
  "error": "Invalid query parameter",
  "message": "limit must be > 0"
}
\`\`\`

**curl Example:**
\`\`\`bash
curl -X GET "http://localhost:8000/api/v1/memories?limit=5&query=agent" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json"
\`\`\`
```

### Common HTTP Methods

| Method | Purpose | Example |
|--------|---------|---------|
| GET | Retrieve data | `GET /memories/{id}` |
| POST | Create resource | `POST /memories` (body) |
| PUT | Replace resource | `PUT /memories/{id}` (full body) |
| PATCH | Update fields | `PATCH /memories/{id}` (partial body) |
| DELETE | Remove resource | `DELETE /memories/{id}` |

## GraphQL API Documentation

### Query Documentation

```markdown
## Query: memories

Fetch memories with pagination and filtering.

**Arguments:**
- \`first\`: Int (default: 10) - Results per page
- \`after\`: String - Cursor for pagination
- \`query\`: String - Search filter
- \`embedding_similarity\`: Float (0-1) - Semantic similarity threshold

**Returns:** MemoryConnection

\`\`\`graphql
query GetMemories($first: Int, $query: String) {
  memories(first: $first, query: $query) {
    edges {
      node {
        id
        content
        createdAt
        embedding
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
\`\`\`

**Variables Example:**
\`\`\`json
{
  "first": 5,
  "query": "neurotransmitter"
}
\`\`\`

**Response:**
\`\`\`json
{
  "data": {
    "memories": {
      "edges": [
        {
          "node": {
            "id": "1",
            "content": "...",
            "createdAt": "2025-10-19T10:30:00Z"
          },
          "cursor": "eyJvZmZzZXQiOiAwfQ=="
        }
      ],
      "pageInfo": {
        "hasNextPage": true,
        "endCursor": "eyJvZmZzZXQiOiA1fQ=="
      },
      "totalCount": 42
    }
  }
}
\`\`\`

**curl Example:**
\`\`\`bash
curl -X POST "http://localhost:8000/graphql" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "query GetMemories($first: Int) { memories(first: $first) { edges { node { id content } } } }",
    "variables": { "first": 5 }
  }'
\`\`\`
```

### Mutation Documentation

```markdown
## Mutation: createMemory

Create new memory entry.

**Arguments:**
- \`input\`: CreateMemoryInput! (required)
  - \`content\`: String! - Memory content
  - \`neurotransmitters\`: [String!] - Associated neurotransmitters

**Returns:** Memory

\`\`\`graphql
mutation CreateMemory($input: CreateMemoryInput!) {
  createMemory(input: $input) {
    id
    content
    createdAt
    embedding
  }
}
\`\`\`

**Variables:**
\`\`\`json
{
  "input": {
    "content": "Important memory",
    "neurotransmitters": ["dopamine", "serotonin"]
  }
}
\`\`\`

**curl Example:**
\`\`\`bash
curl -X POST "http://localhost:8000/graphql" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "query": "mutation CreateMemory($input: CreateMemoryInput!) { createMemory(input: $input) { id content } }",
    "variables": { "input": { "content": "Test", "neurotransmitters": [] } }
  }'
\`\`\`
```

### Subscription Documentation

```markdown
## Subscription: onMemoryCreated

Real-time notification when memory is created.

**Arguments:**
- None

**Returns:** Memory

\`\`\`graphql
subscription OnMemoryCreated {
  onMemoryCreated {
    id
    content
    createdAt
    neurotransmitters {
      name
      weight
    }
  }
}
\`\`\`

**WebSocket Example:**
\`\`\`bash
# Connect WebSocket
wscat -c ws://localhost:8000/graphql \\
  -H "Authorization: Bearer YOUR_TOKEN"

# Send subscription
{"id":"1","type":"start","payload":{"query":"subscription { onMemoryCreated { id content } }"}}

# Receive updates (server-pushed)
{"id":"1","type":"data","payload":{"data":{"onMemoryCreated":{"id":"42","content":"New memory"}}}}
\`\`\`
```

## Error Response Standards

### Standard Error Format

```json
{
  "error": "ValidationError",
  "message": "Input validation failed",
  "details": {
    "field": "email",
    "reason": "Invalid format"
  },
  "requestId": "req-123456",
  "timestamp": "2025-10-19T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Memory retrieved |
| 201 | Created | New memory saved |
| 204 | No Content | Deletion successful |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Memory ID doesn't exist |
| 409 | Conflict | Duplicate entry |
| 422 | Unprocessable | Validation failed |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Internal error |

### GraphQL Error Format

```json
{
  "errors": [
    {
      "message": "Authentication required",
      "extensions": {
        "code": "UNAUTHENTICATED",
        "status": 401
      }
    }
  ],
  "data": null
}
```

## OpenAPI/Swagger Specification

### Minimal OpenAPI 3.0 Spec

```yaml
openapi: 3.0.0
info:
  title: AGI Memory API
  version: 1.0.0
  description: Autonomous memory system with L1/L2/L3 architecture
servers:
  - url: http://localhost:8000
    description: Development

paths:
  /api/v1/memories:
    get:
      operationId: listMemories
      summary: List all memories
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MemoryList'
        '401':
          description: Unauthorized

components:
  schemas:
    Memory:
      type: object
      required:
        - id
        - content
      properties:
        id:
          type: integer
        content:
          type: string
        createdAt:
          type: string
          format: date-time

    MemoryList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Memory'

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### Generate OpenAPI from FastAPI

```python
# FastAPI auto-generates OpenAPI
# File: backend/main.py

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="AGI Memory API",
    version="1.0.0",
    description="Memory system with distributed architecture"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AGI Memory API",
        version="1.0.0",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Access at: http://localhost:8000/openapi.json
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## curl Examples Library

### Authentication

```bash
# Get token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=pass"

# Result: {"access_token": "eyJ0eXAi...", "token_type": "bearer"}

# Use token in subsequent requests
TOKEN="eyJ0eXAi..."
curl -X GET "http://localhost:8000/api/v1/memories" \
  -H "Authorization: Bearer $TOKEN"
```

### CRUD Operations

```bash
# CREATE
curl -X POST "http://localhost:8000/api/v1/memories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "New memory",
    "neurotransmitters": ["dopamine"]
  }'

# READ (single)
curl -X GET "http://localhost:8000/api/v1/memories/1" \
  -H "Authorization: Bearer $TOKEN"

# READ (list)
curl -X GET "http://localhost:8000/api/v1/memories?limit=5&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# UPDATE
curl -X PUT "http://localhost:8000/api/v1/memories/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated memory"}'

# DELETE
curl -X DELETE "http://localhost:8000/api/v1/memories/1" \
  -H "Authorization: Bearer $TOKEN"
```

### Error Handling

```bash
# Test error response (invalid token)
curl -X GET "http://localhost:8000/api/v1/memories" \
  -H "Authorization: Bearer invalid_token" \
  -w "\nHTTP Status: %{http_code}\n"

# Save response to file for inspection
curl -X GET "http://localhost:8000/api/v1/memories" \
  -H "Authorization: Bearer $TOKEN" \
  -o response.json \
  -w "\n%{http_code}"

# Pretty-print JSON response
curl -X GET "http://localhost:8000/api/v1/memories" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## Documentation Tools

```bash
# Swagger Editor
npm install -g swagger-editor-dist
swagger-editor-start

# Redoc (static ReDoc documentation)
npm install -g redoc-cli
redoc-cli build openapi.yaml -o index.html

# Postman
# Import: File → Import → Paste OpenAPI JSON
# Auto-generates Postman collection

# Insomnia
# Import: Ctrl+Shift+I → Paste OpenAPI URL

# API documentation generation
npm install -g spectacle-docs
spectacle openapi.yaml -o docs/
```

## Best Practices

### DO

✅ Document every endpoint with examples
✅ Include curl commands (copy-paste ready)
✅ Show real request/response payloads
✅ Document error cases (4xx/5xx)
✅ Keep examples up-to-date (test monthly)
✅ Version API endpoints (/v1/, /v2/)
✅ Include rate limits & quotas
✅ Document authentication method clearly
✅ Provide SDK examples if applicable

### DON'T

❌ Generic descriptions ("Returns data")
❌ Outdated curl examples (won't run)
❌ Missing error documentation
❌ No pagination examples
❌ Hardcoded IDs without explanation
❌ Missing required parameters
❌ Incomplete type definitions
❌ No timeout/retry guidance

---

**Version:** 2025-10-19 v1 - API Documentation Skill
**For:** DocsKeeper agent + API specs
**Testing:** Monthly validation of curl examples
