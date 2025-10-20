# Security Git Hooks

Quick reference for git pre-commit security hook.

## TL;DR

The project automatically scans all commits for secrets and API keys.

```bash
# Normal workflow - hook runs automatically
git add .
git commit -m "feature"

# Hook blocks if secrets detected
🚫 PRE-COMMIT BLOCKED

# Skip hook (emergency only)
git commit --no-verify
```

## What Gets Blocked

### API Keys
- Anthropic (`sk-ant-*`)
- Voyage
- Cohere
- Generic API_KEY variables
- AWS secrets

### Files
- `.env` files
- `secrets.json`
- `credentials.xml`
- Private keys (`.pem`, `.key`)
- Production config

### Passwords
- Hardcoded DATABASE_URL with credentials
- PASSWORD = "..."
- VPS root password

## If Your Commit Gets Blocked

### Option 1: Fix It (Recommended)

```bash
# Remove the secret from your code
nano config.py  # Remove API_KEY line

# Use environment variables instead
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Stage and commit again
git add config.py
git commit -m "Use env vars for API key"
✅ Pre-commit check passed
```

### Option 2: Move File to .gitignore

```bash
# If it's a config file
echo ".env.local" >> .gitignore

# Remove from git staging
git reset HEAD .env.local

# Commit the .gitignore
git add .gitignore
git commit -m "Ignore .env.local"
✅ Pre-commit check passed
```

### Option 3: Skip Hook (Emergency Only)

```bash
# If you're 100% sure it's safe
git commit --no-verify

# ⚠️ Use sparingly - defeats security check
```

## Best Practices

### ✅ DO

```python
# Use environment variables
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Use .env files (and add to .gitignore)
# .gitignore:
.env
.env.local
.env.*.local

# Use separate config files per environment
config/
├── base.py        # Common (safe)
├── dev.py         # Dev-safe
└── prod.template  # Template only (no secrets)
```

### ❌ DON'T

```python
# Hardcoded API keys
API_KEY = "sk-ant-xyz123abc"  # ❌ BLOCKED

# Commit .env files
# .env                          # ❌ BLOCKED

# Hardcoded passwords
DB_PASSWORD = "MySecret123"    # ❌ BLOCKED
```

## Testing the Hook

### Verify Hook is Active

```bash
# Should print no errors
.git/hooks/pre-commit
✅ Pre-commit check passed
```

### Test with a Fake Secret

```bash
# Create a test file with fake secret
echo 'ANTHROPIC_API_KEY = "sk-ant-test123"' > test.txt

# Stage it
git add test.txt

# Try to commit (should fail)
git commit -m "test"
🚫 PRE-COMMIT BLOCKED

# Clean up
git reset HEAD test.txt
rm test.txt
```

## For Developers

### Install Hook in New Clone

```bash
cd /path/to/agi
scripts/install-hooks.sh
✅ pre-commit hook installed
```

### Deep Security Scan

For comprehensive analysis beyond patterns:

```bash
cd backend
python -m agents.security_scanner

# Output:
{
  "status": "clean",
  "findings": [],
  "count": 0
}
```

## Technical Details

### Performance

- No staged changes: instant
- Typical scan: 200-300ms
- Maximum: 500ms (many files)

### Detection

- **11 API key patterns** monitored
- **10 sensitive file types** blocked
- **2 critical ban phrases** checked

### Implementation

- Pure Bash (no Python overhead)
- 3-stage detection (fast → slow)
- Early exit optimization

## Documentation

Full documentation: `.git/HOOKS_README.md`

## Questions?

Check `.git/HOOKS_README.md` for detailed troubleshooting and examples.

---

**Version:** 1.0 (2025-10-20)
