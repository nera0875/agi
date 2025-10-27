---
name: tech-research
description: Research stack/frameworks via MCP (Context7, Exa, GitHub, WebFetch)
---

# Tech Research - Guide Complet MCP

Research technologique avant conception projet.

## Workflow Standard

**Ordre recommandé** :
1. **Context7** → Docs officielles framework
2. **Exa Code** → Code examples/patterns APIs
3. **GitHub** → Repos populaires (architecture)
4. **Exa Web** → Articles/best practices
5. **WebFetch** → URL spécifique si nécessaire

---

## 1. Context7 - Documentation Frameworks

**Étape 1 : Resolve Library ID**

```
Tool: mcp__upstash-context-7-mcp__resolve-library-id
Params:
  libraryName: "fastapi" | "react" | "nextjs" | "django" etc
Returns:
  - List of matching libraries
  - Format: {id: "/org/project", name: "...", trust_score: 0-10}

Exemples:
  libraryName: "fastapi"
    → {id: "/tiangolo/fastapi", trust_score: 9.5}
  libraryName: "react"
    → {id: "/facebook/react", trust_score: 9.8}
  libraryName: "nextjs"
    → {id: "/vercel/next.js", trust_score: 9.7}
```

**Étape 2 : Get Library Docs**

```
Tool: mcp__upstash-context-7-mcp__get-library-docs
Params:
  - context7CompatibleLibraryID: "/org/project" (from step 1)
  - topic: Optional filter ("routing", "auth", "database", "testing", "deployment")
  - tokens: 5000 (recommandé, max 50000 pour exhaustive)
Returns:
  - Structured documentation
  - Code examples intégrés
  - API patterns officiels
  - Setup instructions

Exemples complets:

# FastAPI Auth
context7CompatibleLibraryID: "/tiangolo/fastapi"
topic: "authentication"
tokens: 5000
→ Retourne patterns JWT, OAuth2, dependencies...

# React Hooks
context7CompatibleLibraryID: "/facebook/react"
topic: "hooks"
tokens: 5000
→ Retourne useState, useEffect, useContext exemples...

# Next.js Routing
context7CompatibleLibraryID: "/vercel/next.js"
topic: "routing"
tokens: 5000
→ Retourne App Router, file-based routing, layouts...
```

**Patterns Utilisation** :
- Toujours résoudre ID d'abord (erreur commune : ID incorrect)
- Topic optionnel mais recommandé pour résultats ciblés
- tokens:5000 = bon équilibre détail/tokens
- tokens:10000+ si exhaustive documentation needed

**Quand utiliser** :
- Framework officiel bien documenté (React, FastAPI, Django)
- Patterns intégrés au framework (routing, auth, DB)
- Syntaxe API récente/changes

**Fallback si fail** :

```
Erreur: resolve-library-id retourne empty list
→ Library pas reconnue ou nom incorrect
→ Action: WebFetch documentation URL officielle
   Ex: https://fastapi.tiangolo.com
→ Alternative: Exa Web "FastAPI official documentation"

Erreur: get-library-docs retourne partial
→ Topic trop spécifique ou pas dans docs
→ Action: Retry sans topic (broad search)
→ Alternative: Exa Code "fastapi [topic] examples"
```

---

## 2. Exa Code - Code Examples APIs

**Tool** :

```
mcp__exa__get_code_context_exa
Params:
  - query: String (semantic code search)
  - tokensNum: 1000-5000 (recommandé 3000)
Returns:
  - Code context from APIs/SDKs
  - Syntax patterns
  - Integration examples
  - Error handling patterns

Exemples queries:

"fastapi jwt authentication setup"
→ Code patterns JWT implementation FastAPI

"react useeffect cleanup dependency array"
→ React hooks patterns, cleanup logic

"python async postgresql connection pool"
→ asyncpg pool initialization, connection handling

"nextjs api routes middleware authentication"
→ API Routes avec middleware + auth

"typescript fetch retry exponential backoff"
→ Client-side retry patterns

"fastapi dependency injection classes models"
→ FastAPI DI patterns pour models

"react query usemutation error handling"
→ React Query error patterns

"django celery task retry config"
→ Django async task patterns
```

**Patterns Utilisation** :
- Query = descripción détaillée (pas juste "react")
- tokensNum:3000 = bon pour 10-15 code examples
- Retourne "code context" = patterns réels de production
- Results = triés par relevance sémantique

**Quand utiliser** :
- Patterns code spécifiques
- Integration APIs tierces
- Setup configurations
- Error handling patterns
- Architecture patterns

**Fallback si fail** :

```
Erreur: No results ou rate limit
→ GitHub search_code avec même query (Voir Section 3)
→ Reducer tokensNum (peut être trop haut)
→ Try alternative query (plus générique)

Erreur: Résultats peu pertinents
→ Préciser davantage query (ajouter contexte framework)
→ Alternative: Exa Web semantic search articles
```

---

## 3. GitHub - Repos Populaires & Code

**Search Repositories** :

```
Tool: mcp__smithery-ai-github__search_repositories
Params:
  - query: String (with filters)
  - per_page: 10-30 (recommandé 10)
Returns:
  - List of repositories
  - Sorted by stars + relevance
  - Include: stars, forks, updated, description

Query Syntax Examples:

"fastapi postgresql stars:>1000"
→ FastAPI + PostgreSQL, 1000+ stars
→ Find proven production patterns

"language:typescript nextjs stars:>1000 created:>2024-01-01"
→ Recent Next.js TypeScript projects
→ Filters: language + stars + date

"react state management alternative:redux"
→ State management libs alternative to Redux

"authentication topic:jwt"
→ JWT authentication patterns

"fastapi react monorepo stars:>500"
→ Full-stack projects FastAPI + React

"docker compose postgresql redis fastapi"
→ Devops setup patterns (Docker Compose)
```

**Get Repository Structure** :

```
Tool: mcp__smithery-ai-github__get_repository
Params:
  - owner: "username"
  - repo: "repo-name"
Returns:
  - README content
  - File tree structure
  - Main.py / main.ts entry point
  - Project architecture overview

Example:
owner: "tiangolo"
repo: "full-stack-fastapi-postgresql"
→ Returns full project structure + documentation
```

**Get File Contents** :

```
Tool: mcp__smithery-ai-github__get_file_contents
Params:
  - owner: "username"
  - repo: "repo-name"
  - path: "src/main.py" or "src/app.tsx"
  - mode: "overview" | "full"
Returns:
  - File content
  - mode: "overview" = first 50 lines + key patterns
  - mode: "full" = complete file (if <5000 lines)

Example:
owner: "vercel"
repo: "next.js"
path: "examples/with-typescript/pages/api/hello.ts"
mode: "overview"
→ Returns first section + type annotations example
```

**Search Code** :

```
Tool: mcp__smithery-ai-github__search_code
Params:
  - q: String (with filters)
Returns:
  - List of matching files
  - File path + preview
  - Line numbers

Query Syntax:
"repo:tiangolo/fastapi path:app extension:py"
→ Find all .py files in app/ folder

"language:python async def type:code"
→ Find async functions in Python

"React.useState import:react"
→ Find useState usage patterns
```

**Workflow Complet GitHub** :

```
1. search_repositories "fastapi postgresql stars:>1000"
   → Retourne top 10 repos (sorted by stars)

2. get_repository owner, repo (pour top 3)
   → Analyse structure dossiers + README
   → Identifie architecture commune
   → Extract: /app, /api, /models, /schemas patterns

3. get_file_contents path="src/main.py" mode="overview" (top repo)
   → Patterns initialization, middleware setup
   → Extract: Dependencies, routes organization

4. Synthèse: Architecture commune identifiée
   - Structure dossiers standard
   - Import patterns
   - Middleware chains
   - Error handling approach
```

**Quand utiliser** :
- Architecture projet réelle (production)
- Structure dossiers standard
- Patterns communauté validés
- Code examples authentiques
- Established best practices

---

## 4. Exa Web - Articles Best Practices

**Tool** :

```
mcp__exa__web_search_exa
Params:
  - query: String (semantic web search)
  - numResults: 5-10 (recommandé 5)
Returns:
  - List of articles/blogs
  - Sorted by semantic relevance
  - Includes: URL, title, snippet

Exemples queries:

"fastapi best practices 2025 production deployment"
→ Recent best practices articles

"react state management zustand vs redux comparison"
→ Framework comparisons + tradeoffs

"fastapi vs flask performance benchmarks"
→ Performance analysis

"nextjs 14 partial prerendering guide tutorial"
→ Feature guides + how-to

"postgresql connection pooling python asyncpg"
→ Database optimization patterns

"typescript strict mode tsconfig best practices"
→ Type safety + configuration guides

"nextjs api routes vs backend framework comparison"
→ Architecture decisions

"fastapi security cors csrf jwt authentication"
→ Security patterns complete guide
```

**Patterns Utilisation** :
- Query = descriptif + année (2025 pour récent)
- numResults:5 = bon pour synthèse
- Results = semantic ranking (plus relevant premier)
- Retourne articles blogs + docs + tutorials

**Quand utiliser** :
- Comparaisons frameworks/libraries
- Best practices récentes
- Performance benchmarks
- Migration guides
- Trade-offs decisions
- Security guides
- Setup tutorials

**Fallback si fail** :

```
Erreur: No results
→ Élargir query (enlever filtres year)
→ Try simpler terms
→ WebFetch docs officielles

Erreur: Rate limit
→ Fallback Context7 docs
→ Try GitHub repos pour patterns
```

---

## 5. WebFetch - URL Spécifique

**Tool** :

```
WebFetch
Params:
  - url: String (specific URL)
  - prompt: String (what to extract)
Returns:
  - Page content analyzed
  - Structured information
  - Code blocks extracted
  - Key patterns identified

Examples:

url: "https://fastapi.tiangolo.com/tutorial/security"
prompt: "Extract authentication patterns and code examples"
→ Returns: OAuth2, JWT patterns, setup code

url: "https://nextjs.org/docs/app/building-your-application/data-fetching"
prompt: "List all data fetching methods with examples"
→ Returns: fetch(), Server Components, Server Actions

url: "https://github.com/some-project/blob/main/README.md"
prompt: "Architecture overview and setup instructions"
→ Returns: Project structure + deployment guide
```

**Patterns Utilisation** :
- URL = précise et connue
- prompt = détaillé (quoi extraire)
- Peut échouer si page JS-heavy ou blocked
- Recommandé pour: offical docs, changelogs, blog posts

**Quand utiliser** :
- URL précise fournie par user
- Changelog framework (latest features)
- Migration guide spécifique
- Blog post technique
- Official documentation page
- GitHub README (architecture)

**Limitations** :
- 1 URL à la fois (pas batch)
- Peut échouer si JavaScript-heavy (SPA)
- Peut être bloqué par robots.txt
- Timeouts si contenu très gros

---

## Patterns Décision Stack

### Backend API

**Workflow Complet** :

```
OBJECTIF: Choisir stack backend optimal

1. Context7 Documentation
   library: "fastapi" → topic: "routing", "authentication"
   library: "django" → topic: "orm", "middleware"
   library: "nodejs-express" → topic: "routing", "async"
   Retourne: Patterns officiels + syntax

2. Exa Code Examples
   query: "fastapi postgresql async models validation"
   query: "django orm database migrations"
   query: "nodejs express middleware error handling"
   Retourne: Code patterns réels

3. GitHub Repos
   search: "fastapi postgresql redis stars:>1000"
   → Top 5 repos, analyse structure
   → Extract: /app/routes, /app/models, /app/schemas patterns
   Retourne: Architecture réelle

4. Exa Web Articles
   query: "fastapi vs django 2025 comparison"
   query: "postgresql connection pooling async python"
   query: "redis caching patterns fastapi"
   Retourne: Best practices + trade-offs

5. Synthèse Décision
   Recommandé: FastAPI + PostgreSQL + Redis
   Alternatives: Django + PostgreSQL, Node.js + Express
   Patterns: Async DB, dependency injection, JWT auth
   Risks: PostgreSQL pool tuning, connection limits
```

**Output JSON** :

```json
{
  "recommended_stack": [
    "FastAPI",
    "PostgreSQL",
    "Redis",
    "Docker",
    "Kubernetes"
  ],
  "alternatives": [
    {
      "name": "Django + PostgreSQL",
      "tradeoffs": "More batteries-included, slower, less async"
    },
    {
      "name": "Node.js + Express",
      "tradeoffs": "JavaScript everywhere, less type-safe"
    }
  ],
  "architecture": {
    "structure": "/app/routes + /app/services + /app/models",
    "async_patterns": "asyncpg, async def routes, background tasks",
    "authentication": "JWT + dependencies injection",
    "database": "PostgreSQL + sqlalchemy async + alembic migrations"
  },
  "patterns": [
    "Dependency injection for DB connections",
    "Async/await for I/O operations",
    "JWT authentication with roles",
    "Redis caching layer",
    "Database connection pooling"
  ],
  "risks": [
    "PostgreSQL connection pool tuning required",
    "Async context in tests (pytest-asyncio)",
    "Transaction handling in concurrent requests"
  ],
  "resources": {
    "docs": [
      "https://fastapi.tiangolo.com",
      "https://www.postgresql.org/docs"
    ],
    "repos": [
      "tiangolo/full-stack-fastapi-postgresql",
      "encode/starlette"
    ],
    "articles": [
      "FastAPI in production patterns",
      "PostgreSQL async best practices"
    ]
  },
  "mcp_sources": {
    "context7": "success (5 docs)",
    "exa_code": "success (15 patterns)",
    "github": "success (top 5 repos)",
    "exa_web": "success (8 articles)"
  }
}
```

### Frontend SPA (React/Vue/Next.js)

**Workflow** :

```
1. Context7: "/vercel/next.js" topic:"routing"
2. Exa Code: "nextjs 14 server actions form handling"
3. GitHub: search "nextjs typescript tailwind stars:>1000"
4. Exa Web: "nextjs 14 vs remix comparison"
5. Synthèse: Next.js 14 App Router + Server Actions
```

**Output** :

```json
{
  "recommended_stack": [
    "Next.js 14 (App Router)",
    "TypeScript",
    "Tailwind CSS",
    "React Query (data fetching)",
    "Zustand (state management)"
  ],
  "architecture": {
    "structure": "app/ directory with Server Components",
    "data_fetching": "Server Actions + fetch()",
    "state": "Zustand for client state only"
  },
  "patterns": [
    "Server Components by default",
    "Server Actions for mutations",
    "Layout nesting",
    "Dynamic segments"
  ]
}
```

### Fullstack (Frontend + Backend)

**Workflow** :

```
1. Context7: "/tiangolo/fastapi" + "/vercel/next.js"
2. Exa Code: "fastapi nextjs api integration typescript"
3. GitHub: search "fastapi nextjs monorepo stars:>500"
4. Synthèse: Monorepo structure + API patterns
```

**Output** :

```json
{
  "recommended_stack": [
    "Next.js 14 (frontend)",
    "FastAPI (backend)",
    "PostgreSQL",
    "Docker Compose"
  ],
  "monorepo_structure": {
    "frontend/": "Next.js 14 app",
    "backend/": "FastAPI application",
    "docker-compose.yml": "Local development"
  },
  "api_patterns": "REST API, JSON request/response",
  "development": "Hot reload both frontend and backend"
}
```

---

## Fallback Chains

### Context7 Fail

```
Scenario: resolve-library-id returns empty
├─ Primary fail: Library name not recognized
├─ Fallback 1: WebFetch official docs
│  → url: "https://[framework].io/docs"
│  → prompt: "Overview and setup guide"
└─ Fallback 2: Exa Web
   → query: "[framework] official documentation"
```

### Exa Code Fail

```
Scenario: No results or rate limit
├─ Fallback 1: GitHub search_code
│  → Same query terms
│  → Finds real code in repositories
├─ Fallback 2: GitHub get_file_contents
│  → From top repo (from search_repositories)
│  → mode: "overview" for patterns
└─ Fallback 3: Context7
   → Topic specific to use case
```

### GitHub Fail

```
Scenario: API rate limit or timeout
├─ Fallback 1: Exa Code
│  → query: "[project] [pattern]"
├─ Fallback 2: Exa Web
│  → query: "[project] architecture patterns"
└─ Fallback 3: WebFetch
   → Known repo URL (if available)
```

### Exa Web Fail

```
Scenario: No results
├─ Fallback 1: Broader query (remove year/specifics)
├─ Fallback 2: Context7 official docs
├─ Fallback 3: GitHub search_repositories
   → Comments and discussions in PRs
└─ Fallback 4: WebFetch
   → Known docs URL
```

---

## Error Handling

**Rate Limits** :

```
Context7:
  → Wait 1 minute OR
  → Switch to WebFetch docs directly

Exa:
  → Fall back to GitHub search_code
  → Reduce tokensNum/numResults
  → Try simpler query

GitHub:
  → Fall back to Exa Code/Web
  → Reduce per_page parameter
  → Try broader search
```

**No Results** :

```
Strategy:
  1. Simplify query (remove specific terms)
  2. Remove date/version filters
  3. Use different MCP tool
  4. WebFetch if URL known
  5. Report to user: "Framework not well documented"
```

**Parsing Errors** :

```
Action:
  - Log warning with query + tool
  - Continue with partial results
  - Try fallback chain
  - Notify user if critical info missing
```

---

## Output Format Standard (All Research)

```json
{
  "research_query": "What backend stack for Django learning project",
  "recommended_stack": [
    "Framework/tool 1",
    "Framework/tool 2"
  ],
  "alternatives": [
    {
      "name": "Alternative 1",
      "tradeoffs": "Why different",
      "pros": ["pro1"],
      "cons": ["con1"]
    }
  ],
  "architecture": {
    "structure": "Folder structure overview",
    "core_patterns": "Main design patterns",
    "technology_layers": "Frontend/backend/database"
  },
  "patterns": [
    "Pattern 1 description",
    "Pattern 2 description"
  ],
  "risks": [
    "Risk 1 (mitigation)",
    "Risk 2 (mitigation)"
  ],
  "learning_path": [
    "Step 1: Setup environment",
    "Step 2: Create basic project"
  ],
  "resources": {
    "official_docs": ["url1"],
    "github_repos": ["owner/repo"],
    "articles": ["article title"],
    "tutorials": ["tutorial link"]
  },
  "mcp_sources": {
    "context7": "success|partial|failed (count)",
    "exa_code": "success|partial|failed (count)",
    "github": "success|partial|failed (count)",
    "exa_web": "success|partial|failed (count)",
    "webfetch": "success|partial|failed (count)"
  }
}
```

---

## Utilisation Rapide

**30 secondes research** :
```
→ Context7 (1-2 topics)
→ GitHub search_repositories (star filtering)
→ Synthèse rapide
```

**5 minutes research** :
```
→ Context7 complet
→ GitHub repos + files
→ Exa Code + Web
→ Synthèse détaillée
```

**Production research** :
```
→ Tous MCPs
→ Fallback chains complètes
→ Exhaustive patterns
→ Risks + migration paths
```
