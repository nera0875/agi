---
name: README Health Check
description: Audit README structure, freshness, and quality criteria
category: documentation
---

# README Health Check

Expertise in auditing README.md files for completeness, structure, and maintenance quality.

## Quality Criteria

### Structure Requirements (MUST HAVE)

**1. Header Section**
- Project title (h1: `# Project Name`)
- One-line description (summary)
- Badge area (status, CI/CD, coverage)

```markdown
# AGI Memory System

Autonomous agent team managing distributed memory (L1/L2/L3) with semantic embeddings.

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
```

**2. Quick Start Section**
- Prerequisites (Node.js, Python, PostgreSQL versions)
- Installation command
- Running the project
- Environment setup (.env example)

```markdown
## Quick Start

**Prerequisites:**
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

**Installation:**
\`\`\`bash
# Clone repo
git clone <repo>

# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
\`\`\`

**Run:**
\`\`\`bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend
npm run dev
\`\`\`
```

**3. Features Section**
- Main features (bullet list with brief description)
- Links to detailed docs if complex
- 5-10 key features max

```markdown
## Features

- **Distributed Memory:** L1 (Redis) / L2 (PostgreSQL) / L3 (Neo4j)
- **Autonomous Agents:** 6 specialized agents managing system
- **GraphQL API:** Real-time subscriptions, type-safe queries
- **Semantic Search:** Voyage AI embeddings
- **Cost Optimized:** Haiku for fast agent iterations
```

**4. Project Structure Section**
- High-level directory overview
- Key directories explained (3-4 levels max)

```markdown
## Project Structure

\`\`\`
agi/
├── backend/            FastAPI + GraphQL services
├── frontend/           React 18 + TypeScript + Vite
├── cortex/             MCP tools orchestration
├── agents/             Autonomous agent team
└── docs/               Architecture + guides
\`\`\`
```

**5. API Documentation Section**
- Link to full API docs (separate file or tool)
- Basic example (GraphQL query or REST)
- Authentication method

```markdown
## API

Full API docs: [docs/api.md](docs/api.md)

**GraphQL Query:**
\`\`\`graphql
query GetMemories {
  memories(first: 10) {
    id
    content
    embedding
  }
}
\`\`\`
```

**6. Contributing Section**
- Development setup
- Code style guide
- Branch naming convention
- PR process

```markdown
## Contributing

1. Fork repository
2. Create branch: \`git checkout -b feature/your-feature\`
3. Follow code style: \`npm run lint\`
4. Write tests: \`npm run test\`
5. Submit PR with description

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
```

**7. Troubleshooting Section**
- Common errors + solutions
- FAQ
- Links to issues/discussions

```markdown
## Troubleshooting

**Q: PostgreSQL connection fails?**
A: Check \`.env\` DATABASE_URL and ensure PostgreSQL is running.

**Q: Redis timeout?**
A: Verify Redis service: \`redis-cli ping\` should return PONG.

See [docs/troubleshooting.md](docs/troubleshooting.md) for more.
```

**8. License & Credits**
- License type (MIT, Apache, etc)
- Attribution if forked
- Contact info

```markdown
## License

MIT License - See [LICENSE](LICENSE) file

## Credits

Built by AGI Team | Contact: contact@example.com
```

## Freshness Indicators

### RED FLAGS (Update Immediately)

| Issue | Impact |
|-------|--------|
| Last updated 6+ months ago | Likely outdated dependencies |
| Python 2.7 or Node.js 12 mentioned | Security risk |
| Breaking APIs changed in code but not README | Developers confused |
| Setup instructions fail (tested) | Lost contributors |

### Maintenance Cycle

```
✅ Green:    Updated within last month
🟡 Yellow:   2-3 months old (review soon)
🔴 Red:      6+ months old (update NOW)
```

### Auto-Check Script

```bash
# README age
stat README.md | grep Modify

# Dependency freshness
head -20 requirements.txt | grep "="
npm ls --depth=0 2>/dev/null | grep "deduped"
```

## Quality Scoring

### Perfect README (100%)
- ✅ All 8 sections present
- ✅ Setup tested & working
- ✅ Updated within 2 weeks
- ✅ Code examples run as-is
- ✅ Links (internal/external) not broken
- ✅ Clear headings (h2, h3 hierarchy)
- ✅ TypeScript/Python code blocks specified
- ✅ Badges accurate

### Good README (80%)
- ✅ 7/8 sections (1 optional: Troubleshooting)
- ✅ Setup mostly working (1-2 issues)
- ✅ Updated within month
- ✅ Broken links < 10%
- ✅ Proper headings

### Needs Work (< 80%)
- ❌ Missing 2+ sections
- ❌ Setup broken
- ❌ Not updated in 3+ months
- ❌ Multiple broken links
- ❌ Outdated dependencies

## Audit Checklist

When reviewing README:

```markdown
□ Header: Title + description + badges
□ Prerequisites: Specific versions listed
□ Quick Start: Copy-paste ready (tested)
□ Features: 5-10 items with descriptions
□ Structure: Clear directory layout
□ API: Query/mutation examples
□ Contributing: Branch + PR process
□ Troubleshooting: Common issues covered
□ License: Type + file present
□ Freshness: Updated < 2 weeks
□ Links: All working
□ Code blocks: Language specified (\`\`\`python etc)
□ No formatting errors
□ Accessible (alt text for images)
```

## Tools & Commands

```bash
# Check markdown syntax
npm install -g markdownlint-cli
markdownlint README.md

# Check broken links
npm install -g markdown-link-check
markdown-link-check README.md

# GitHub README preview
# Commit test file, view in GitHub (web UI)

# Local preview
pandoc README.md -o README.html
open README.html
```

## Common Mistakes to Avoid

❌ **Too Long:** > 2000 lines (split into docs/)
❌ **No Code Examples:** Theory without practice
❌ **Outdated Versions:** "Node 12+" but codebase uses 18
❌ **Broken Setup:** Instructions fail mid-way
❌ **No Table of Contents:** Hard to navigate
❌ **Jargon Without Explanation:** Lost beginners
❌ **Missing Links to Detailed Docs**
❌ **Status badges not auto-updated**

---

**Version:** 2025-10-19 v1 - README Health Check Skill
**For:** DocsKeeper agent + manual audits
**Review Frequency:** Every 2 weeks
