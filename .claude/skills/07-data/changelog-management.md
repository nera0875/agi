---
name: Changelog Management
description: Keep a Changelog format, categorization, and maintenance patterns
category: documentation
---

# Changelog Management

Expertise in maintaining CHANGELOG.md following Keep a Changelog format, semantic versioning, and release management.

## Keep a Changelog Format

### Correct Structure

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- New user features being developed

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future

### Removed
- Features removed this cycle

### Fixed
- Bug fixes

### Security
- Security vulnerabilities fixed

## [1.0.0] - 2025-10-19

### Added
- Initial release with memory system L1/L2/L3
- GraphQL API with queries and mutations
- 6 autonomous agents (CodeGuardian, InfraWatch, DebtHunter, SecuritySentinel, DocsKeeper, PerformanceOptimizer)
- Redis cache layer (L1)
- PostgreSQL storage (L2)
- Neo4j graph database (L3)
- Voyage AI embeddings integration
- Real-time subscriptions via WebSocket

### Changed
- N/A (initial release)

### Security
- Implemented Bearer token authentication
- Added secret management via .env

## [0.9.0] - 2025-10-15

### Added
- Beta memory consolidation pipeline
- Experimental GraphQL subscriptions
- Performance monitoring dashboard

### Fixed
- Memory leak in Redis connection pool
- Incorrect neurotransmitter weighting

### Known Issues
- WebSocket disconnects after 30 min of inactivity (FIX: upgrade to 1.0.0)

---

[Unreleased]: https://github.com/user/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/repo/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/user/repo/releases/tag/v0.9.0
```

## Category Guidelines

### [Added]

**For new features or functionality.**

✅ **Good examples:**
```
- Memory consolidation from L1 to L2 cache
- GraphQL subscription for real-time memory updates
- Voyage AI embeddings for semantic search
- New autonomous agent: PerformanceOptimizer
- Support for custom neurotransmitter weighting
```

❌ **Avoid:**
```
- Added stuff
- More features
- Improvements (too vague)
```

**Template:**
```markdown
### Added
- [Feature name]: [Brief description of capability]
- [Feature name]: [What user can now do]
- CLI command: `agent-cli run [type]` for agent execution
```

### [Changed]

**For changes to existing functionality.**

✅ **Good examples:**
```
- Refactored memory service from synchronous to async/await
- Changed GraphQL schema: `Memory.embedding` now returns vector type
- Improved consolidation algorithm from O(n²) to O(n log n)
- Updated Redis TTL from 1 hour to 6 hours for L1 cache
```

❌ **Avoid:**
```
- Made improvements
- Updated code
- Performance tweaks (unspecific)
```

**Template:**
```markdown
### Changed
- [What changed]: From [old] to [new]
- [Component]: [Specific behavioral change]
- API endpoint: `/api/memories` now returns paginated results
```

### [Deprecated]

**For soon-to-be removed features.**

✅ **Good examples:**
```
- REST API in favor of GraphQL (remove in v2.0)
- Memory consolidation via cron (switch to event-driven by v1.5)
- `memory.get_sync()` method (use `async def get()` instead)
```

❌ **Avoid:**
```
- Old code
- Legacy features
```

**Template:**
```markdown
### Deprecated
- [Feature]: Deprecated in favor of [replacement] (will remove in [version])
- [Method]: Use [alternative] instead
```

### [Removed]

**For removed features in this version.**

✅ **Good examples:**
```
- Removed SQLite support (PostgreSQL only now)
- Removed `legacy_consolidation()` method (use `consolidation.py` instead)
- Removed deprecated REST endpoints (use GraphQL)
```

❌ **Avoid:**
```
- Removed old stuff
- Cleaned up
```

**Template:**
```markdown
### Removed
- [Feature]: Removed in favor of [reason/replacement]
- [Endpoint]: `/api/legacy/memories` endpoint removed
```

### [Fixed]

**For bug fixes.**

✅ **Good examples:**
```
- Fixed memory leak in Redis connection pool (connections not released)
- Fixed race condition in embedding consolidation causing duplicates
- Fixed GraphQL query timeout when memory.embedding returns large vectors
```

❌ **Avoid:**
```
- Fixed bugs
- Fixed various issues
```

**Template:**
```markdown
### Fixed
- [Bug description]: Now [expected behavior]
- Issue #123: [What's fixed]
- Fixed [symptom] caused by [root cause]
```

### [Security]

**For security vulnerabilities or hardening.**

✅ **Good examples:**
```
- Fixed SQL injection vulnerability in memory search query
- Added rate limiting (100 req/min per IP) to prevent API abuse
- Updated Anthropic API key handling to use .env only (never commit)
```

❌ **Avoid:**
```
- Made security improvements
- Fixed vulnerability
```

**Template:**
```markdown
### Security
- Fixed CVE-2025-1234: [Vulnerability description]
- [Type of vulnerability]: [How it's fixed]
```

## Semantic Versioning

### Format: MAJOR.MINOR.PATCH

| Type | When | Example |
|------|------|---------|
| MAJOR | Breaking changes (incompatible API changes) | 0.9.0 → 1.0.0 (GraphQL schema changed) |
| MINOR | New features (backward compatible) | 1.0.0 → 1.1.0 (Added subscriptions) |
| PATCH | Bug fixes (backward compatible) | 1.0.0 → 1.0.1 (Fixed memory leak) |

### Special Versions

| Version | Meaning |
|---------|---------|
| 0.x.y | Pre-release (unstable API) |
| 1.0.0 | First stable release |
| x.y.z-alpha | Alpha testing |
| x.y.z-beta | Beta testing |
| x.y.z-rc1 | Release candidate |

### Version Bump Decision Tree

```
Changed backward-incompatible API? → MAJOR++
Added features (backward-compat)? → MINOR++
Fixed bugs only? → PATCH++
All changes backward-compatible? → MINOR or PATCH (not MAJOR)
```

## Release Process

### Before Release

```bash
# 1. Update version in files
sed -i 's/version = "1.0.0"/version = "1.0.1"/' pyproject.toml
sed -i 's/"version": "1.0.0"/"version": "1.0.1"/' package.json

# 2. Create [X.Y.Z] section in CHANGELOG.md
# Move content from [Unreleased] to [X.Y.Z] - DATE

# 3. Run final tests
pytest backend/
npm run test

# 4. Build artifacts
python -m build
npm run build

# 5. Commit & tag
git add .
git commit -m "Release v1.0.1"
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin main --tags
```

### Changelog Entry Template

```markdown
## [1.0.1] - 2025-10-20

### Added
- [Feature]: [Description]
- CLI option: `--verbose` for detailed logging

### Changed
- [What changed]: Performance improved 2x
- Memory consolidation: Now processes in batches of 1000 (was 100)

### Fixed
- Memory leak in WebSocket connection cleanup
- Race condition in concurrent embedding calls

### Security
- Added input validation to prevent XSS in graphql queries

---

[1.0.1]: https://github.com/user/repo/compare/v1.0.0...v1.0.1
```

## Tools & Commands

### GitHub Release Integration

```bash
# Create release from git tag (auto-generates from commits)
gh release create v1.0.1 \
  --title "Version 1.0.1" \
  --notes-file CHANGELOG.md

# Draft release (requires manual publish)
gh release create v1.0.1 --draft

# Upload artifacts to release
gh release upload v1.0.1 backend-1.0.1.tar.gz
```

### Automatic Changelog Generation (Conventional Commits)

```bash
# If using conventional commits (feat:, fix:, etc)
npm install -g conventional-changelog-cli

conventional-changelog -p angular -i CHANGELOG.md -s
# Reads git history and auto-generates changelog

# Manual commit message format
# feat: Add memory embeddings
# fix: Resolve race condition in consolidation
# BREAKING CHANGE: GraphQL schema changed
```

### Validate Changelog Format

```python
# Script: scripts/validate_changelog.py
import re

def validate_changelog(file_path: str) -> bool:
    with open(file_path) as f:
        content = f.read()

    # Check structure
    patterns = [
        r'# Changelog',
        r'## \[Unreleased\]',
        r'### Added|Changed|Deprecated|Removed|Fixed|Security',
        r'## \[\d+\.\d+\.\d+\]'
    ]

    for pattern in patterns:
        if not re.search(pattern, content):
            print(f"Missing: {pattern}")
            return False

    print("Changelog format valid")
    return True

if __name__ == "__main__":
    validate_changelog("CHANGELOG.md")
```

## Maintenance Schedule

### When to Release

| Trigger | Action | Timeline |
|---------|--------|----------|
| Critical security fix | Patch release (1.0.1) | Immediate |
| Multiple bug fixes | Patch release (1.0.1) | Weekly |
| New features | Minor release (1.1.0) | Bi-weekly |
| Breaking changes | Major release (2.0.0) | Quarterly |

### Changelog Update Rules

| Event | Action |
|-------|--------|
| New feature merged | Add to [Unreleased] → Added |
| Bug fix merged | Add to [Unreleased] → Fixed |
| API breaking change | Add to [Unreleased] → Changed + MIGRATION GUIDE |
| Feature deprecated | Add to [Unreleased] → Deprecated |

### Weekly Maintenance

```bash
# Check for uncommitted changes
ls -la CHANGELOG.md

# Validate format
python scripts/validate_changelog.py

# Preview release
git log --oneline v1.0.0..HEAD
```

## Common Patterns

### Entry Length

❌ **Too brief (unclear):**
```
- Fixed bug
- Added feature
```

✅ **Good (clear impact):**
```
- Fixed memory leak in Redis connection pool (connections not released on disconnect)
- Added pagination support to GraphQL queries (limit/offset pattern)
```

### Linking Issues

```markdown
### Fixed
- Memory consolidation race condition (#42, #89)
- Fixed: Duplicate embeddings created on concurrent writes (closes #42)
```

### Migration Guide (Breaking Changes)

```markdown
## [2.0.0] - 2025-11-01

### Changed - BREAKING

GraphQL schema restructured. Migration required:

**Before (v1.0):**
\`\`\`graphql
query {
  memory(id: 1) {
    id
    text
  }
}
\`\`\`

**After (v2.0):**
\`\`\`graphql
query {
  memory(id: 1) {
    id
    content  # 'text' renamed to 'content'
  }
}
\`\`\`

**Migration:** Update all GraphQL queries replacing `text` with `content`.
```

## Best Practices

### DO

✅ Update before releasing
✅ Use clear, imperative language ("Add", "Fix", "Remove")
✅ Include issue numbers (#123)
✅ Group similar changes together
✅ Keep [Unreleased] section updated continuously
✅ Link to detailed documentation for complex changes
✅ Mention breaking changes prominently
✅ Include migration guides for major versions

### DON'T

❌ Write after release (retroactive changelog)
❌ Mix vague language ("improvements", "tweaks")
❌ Leave [Unreleased] empty for weeks
❌ Forget to move [Unreleased] to version on release
❌ Commit changes without updating changelog
❌ Use commit hashes as descriptions
❌ Combine multiple breaking changes without clear docs

## Template Repository

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- [NEW FEATURES]

### Changed
- [BEHAVIORAL CHANGES]

### Deprecated
- [FEATURES SOON REMOVED]

### Removed
- [FEATURES REMOVED THIS VERSION]

### Fixed
- [BUG FIXES]

### Security
- [SECURITY FIXES]

## [1.0.0] - YYYY-MM-DD

### Added
- Initial release

---

[Unreleased]: https://github.com/user/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/repo/releases/tag/v1.0.0
```

---

**Version:** 2025-10-19 v1 - Changelog Management Skill
**For:** DocsKeeper agent + release management
**Reference:** https://keepachangelog.com/ + https://semver.org/
