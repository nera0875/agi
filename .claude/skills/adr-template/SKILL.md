---
name: adr-template
description: Architecture Decision Records - template + guide création
---

# ADR Template - Architecture Decision Records

Standard documentation décisions architecture critiques.

## Concept

ADR = markdown document traçant **pourquoi** décision prise (pas juste **quoi**).

## Structure Standard

```markdown
# ADR-XXX: [Titre Décision]

**Status**: Proposed | Accepted | Deprecated | Superseded
**Date**: YYYY-MM-DD
**Deciders**: [tech-lead, advisor, user]
**Context**: [3-5 phrases expliquant besoin business]

## Decision

[Choix final en 1-2 phrases]

## Context Détaillé

**Problème** : [Pourquoi on cherche solution]
**Contraintes** : [Performance, coût, team expertise, timeline]
**Assumptions** : [Ce qu'on suppose vrai]

## Options Considérées

### Option 1: [Nom Solution]
**Pros** :
- Pro 1
- Pro 2

**Cons** :
- Con 1
- Con 2

**Benchmarks** :
- Performance: X req/s
- Memory: Y MB
- Cost: Z$/month

### Option 2: [Alternative]
[Same structure]

### Option 3: [Alternative]
[Same structure]

## Evaluation Matrix

| Criteria       | Weight | Option 1 | Option 2 | Option 3 |
|----------------|--------|----------|----------|----------|
| Performance    | 30%    | 9/10     | 7/10     | 8/10     |
| Team Expertise | 25%    | 8/10     | 5/10     | 6/10     |
| Ecosystem      | 20%    | 7/10     | 9/10     | 8/10     |
| Cost           | 15%    | 6/10     | 8/10     | 7/10     |
| Maintenance    | 10%    | 8/10     | 6/10     | 7/10     |
| **TOTAL**      | 100%   | **8.0**  | **7.1**  | **7.4**  |

## Decision Rationale

**Choix** : Option 1 ([Nom])

**Justification** :
- Raison 1 (scoring + criteria)
- Raison 2 (benchmarks)
- Raison 3 (team/business fit)

**Trade-offs Acceptés** :
- Trade-off 1
- Trade-off 2

## Consequences

**Positives** :
- Conséquence positive 1
- Conséquence positive 2

**Négatives** :
- Risque 1 + mitigation plan
- Risque 2 + mitigation plan

**Neutral** :
- Impact neutre 1

## Implementation Plan

1. Step 1 (timeline)
2. Step 2 (timeline)
3. Migration plan si needed

## Validation

**Tests** : [Comment valider décision]
**Metrics** : [KPIs pour mesurer success]
**Review Date** : [Quand re-évaluer - 6 mois typique]

## References

- [Source 1 - benchmark article]
- [Source 2 - GitHub repo]
- [Source 3 - documentation]
- [Source 4 - Stack Overflow survey]

## Notes

[Informations additionnelles, discussions, alternatives futures]
```

## Naming Convention

Format: `XXX-short-decision-name.md`
- XXX = numéro séquentiel (001, 002, ...)
- short-decision-name = kebab-case descriptif
- Examples:
  - `001-backend-framework.md`
  - `002-database-choice.md`
  - `003-authentication-strategy.md`

## Workflow Création ADR

1. **Tech-lead research** (MCP tools)
2. **Populate template** (options + benchmarks)
3. **Evaluation matrix** (scoring)
4. **Draft ADR** (.plan/adr/XXX-*.md)
5. **Advisor review** (validation historique)
6. **Update state.json** (architecture_decisions field)
7. **Constructor uses ADR** (génère architecture.md)

## Status Lifecycle

```
Proposed → (Advisor review) → Accepted → (Implementation) → Implemented
                                ↓
                            Rejected
                                ↓
                         (Time passes)
                                ↓
                          Deprecated → Superseded by ADR-YYY
```

## Examples

### ADR-001: Backend Framework Choice

**Status**: Accepted
**Date**: 2025-10-27

**Decision**: FastAPI

**Options**: FastAPI (8.0), Django REST (7.1), Flask (7.4)

**Rationale**: Performance (9/10) + team Python expertise (8/10) wins over Django maturity.

**Consequences**:
- ✅ 5x faster than Django (25k vs 5k req/s)
- ⚠️ Less mature ecosystem (mitigation: stick to official plugins)
- ⚠️ Team learning curve 2 weeks (mitigation: training budget)

## Fields Obligatoires

- ✅ Status
- ✅ Date
- ✅ Decision (1-2 phrases)
- ✅ Options (≥2)
- ✅ Evaluation matrix
- ✅ Rationale
- ✅ Consequences
- ✅ References

## Output Location

**Directory**: `.plan/adr/`
**Format**: Markdown
**Naming**: `001-decision-name.md`
