---
name: benchmark-patterns
description: Patterns benchmarks comparatifs solutions techniques
---

# Benchmark Patterns - Methodology Comparaison

Méthodologie benchmarks robustes pour décisions tech.

## Concept

Comparer solutions avec **données mesurables**, pas opinions.

## Dimensions Benchmark

### 1. Performance

**Metrics** :
- Throughput (req/s, queries/s)
- Latency (p50, p95, p99 ms)
- Memory footprint (MB RAM)
- CPU usage (% cores)
- Scalability (linear/sublinear)

**Tools** :
- HTTP: wrk, k6, Apache Bench
- DB: sysbench, pgbench
- Load: Locust, Gatling

**Methodology** :
```bash
# Example FastAPI benchmark
wrk -t12 -c400 -d30s http://localhost:8000/api/endpoint
# Output: Requests/sec, Latency distribution
```

**Reporting** :
```json
{
  "framework": "FastAPI",
  "requests_per_sec": 25000,
  "latency_p50": 15,
  "latency_p95": 45,
  "latency_p99": 120,
  "memory_mb": 180
}
```

### 2. Developer Experience (DX)

**Metrics** :
- Time to "Hello World" (minutes)
- Documentation completeness (1-10 score)
- Error messages clarity (examples count)
- Type safety (static typing %)
- IDE support (autocomplete quality)

**Methodology** :
1. Fresh project setup (timer start)
2. Implement simple feature
3. Debug intentional error
4. Rate experience (1-10 scale)

**Reporting** :
```json
{
  "framework": "FastAPI",
  "hello_world_minutes": 5,
  "docs_score": 9,
  "type_safety": "full",
  "error_messages": "excellent",
  "dx_score": 8.5
}
```

### 3. Ecosystem

**Metrics** :
- GitHub stars (popularity)
- Contributors count (community)
- Recent commits (maintenance)
- Open issues response time (support)
- Plugins/extensions count
- NPM/PyPI downloads trend (6 months)
- Stack Overflow questions (adoption)
- Security advisories (CVE count)

**Sources** :
- GitHub API
- NPM trends / PyPI stats
- Stack Overflow Trends
- Snyk / CVE databases

**Reporting** :
```json
{
  "library": "FastAPI",
  "github_stars": 75000,
  "contributors": 500,
  "recent_commits_30d": 150,
  "pypi_downloads_monthly": 5000000,
  "stackoverflow_questions": 12000,
  "cve_count": 2,
  "ecosystem_score": 9.0
}
```

### 4. Cost

**Metrics** :
- Infrastructure cost ($/month 10k users)
- License fees
- Developer hours (implementation time)
- Training cost (team onboarding)

**Methodology** :
```
Cost = Infra + License + (Dev_hours × hourly_rate) + Training
```

**Reporting** :
```json
{
  "solution": "FastAPI + PostgreSQL",
  "infra_monthly_usd": 50,
  "license_fees": 0,
  "implementation_hours": 80,
  "training_hours": 16,
  "total_first_year_usd": 14400
}
```

### 5. Team Fit

**Metrics** :
- Current expertise (team members count)
- Learning curve (weeks to proficiency)
- Hiring pool (candidates available)
- Onboarding time (new dev productive)

**Methodology** :
- Survey team: "Rate expertise 1-10"
- Estimate learning time (expert opinion)
- Check job boards (candidates count)

**Reporting** :
```json
{
  "technology": "Python/FastAPI",
  "team_expertise_avg": 7.5,
  "learning_curve_weeks": 2,
  "hiring_pool": "large",
  "team_fit_score": 8.0
}
```

## Benchmark Workflow

```
1. Define criteria (performance, DX, cost, etc.)
2. Weight criteria (totals 100%)
3. Create POC minimal (each solution)
4. Run benchmarks (standardized)
5. Collect metrics
6. Score each solution (1-10)
7. Calculate weighted total
8. Document in ADR
```

## Evaluation Matrix Template

| Criteria       | Weight | Sol 1 | Sol 2 | Sol 3 |
|----------------|--------|-------|-------|-------|
| Performance    | 30%    | 9/10  | 7/10  | 8/10  |
| Team Expertise | 25%    | 8/10  | 5/10  | 6/10  |
| Ecosystem      | 20%    | 7/10  | 9/10  | 8/10  |
| Cost           | 15%    | 6/10  | 8/10  | 7/10  |
| DX             | 10%    | 8/10  | 6/10  | 7/10  |
| **TOTAL**      | 100%   | **8.0**| **7.1**| **7.4**|

**Calculation** :
```
Sol1 = (9×0.30) + (8×0.25) + (7×0.20) + (6×0.15) + (8×0.10)
     = 2.70 + 2.00 + 1.40 + 0.90 + 0.80
     = 8.0
```

## Output Format

```json
{
  "benchmarks": [
    {
      "solution": "FastAPI",
      "performance": {"req_s": 25000, "latency_p95": 45},
      "dx": {"score": 8.5},
      "ecosystem": {"score": 9.0},
      "cost": {"monthly_usd": 50},
      "team_fit": {"score": 8.0},
      "weighted_score": 8.0
    },
    {
      "solution": "Django REST",
      "performance": {"req_s": 5000, "latency_p95": 120},
      "dx": {"score": 7.0},
      "ecosystem": {"score": 9.5},
      "cost": {"monthly_usd": 60},
      "team_fit": {"score": 9.0},
      "weighted_score": 7.1
    }
  ],
  "winner": "FastAPI",
  "margin": 0.9
}
```

## Integration with ADR

**ADR references benchmarks** :
- Evaluation matrix → Scoring section
- Benchmarks JSON → Options détaillées
- Winner determination → Decision rationale

**Workflow** :
1. Run benchmarks → benchmarks.json
2. Create ADR → Reference benchmarks.json
3. Score options → Evaluation matrix
4. Document rationale → Links to benchmark sources
