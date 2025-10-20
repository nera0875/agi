---
name: "Memory Strategy"
description: "Quand stocker quoi où (L1/L2/L3) après chaque tâche. Rules consolidation automatique."
categories: ["system", "memory", "strategy"]
tags: ["L1", "L2", "L3", "consolidation", "storage", "persistence"]
version: "1.0.0"
enabled: true
---

## Overview

Stratégie de stockage mémoire pour l'AGI : décider intelligemment quelle layer utiliser (L1/L2/L3) pour chaque type de donnée, et automatiser la consolidation mémoire.

## When to use

- Après tâche importante complétée
- Décision architecturale prise
- Pattern détecté 5+ fois
- Avant context compact (hooks)

## Quick rules

| Données | Layer | Condition |
|---------|-------|-----------|
| Résultat important | L2 (PostgreSQL) | Besoin retrieval rapide + historique |
| Décision architecturale | L3 (Neo4j) + ADR | Décision stratégique, patterns |
| Pattern répété 5x | L3 + Skill | Créer skill si récurrent |
| Contexte urgent | L1 (Redis) | Très temporaire, <5min |
| Status d'exécution | L1 seulement | Task en cours, volatile |

## Core Concepts

### L1 (Redis) - Ephemeral Cache
- **TTL:** 5 minutes max
- **Usecases:** Status tâche en cours, temp results, notifications
- **Éviter:** Données importantes
- **Exemple:** `task_status: {task_id: "...", progress: 45}`

### L2 (PostgreSQL) - Persistent Memory
- **Retention:** Long-term (mois)
- **Usecases:** Résultats importants, insights, analyses
- **Schema:** `memory_events` + `memory_retrieval_log`
- **Exemple:** `{"type": "insight", "content": "Backend a 10 fichiers >500 lignes", "source": "debt_hunter"}`

### L3 (Neo4j) - Knowledge Graph
- **Nodes:** Concepts, architectures, decisions
- **Relations:** DEPENDS_ON, IMPLEMENTS, CONFLICTS_WITH
- **Usecases:** Architecture decisions, patterns, relationships
- **Exemple:** `(Decision:ArchitectureDecision) -IMPLEMENTS-> (Pattern:async_await_storage)`

## Storage Decision Tree

```
┌─ Résultat important ?
│  ├─ OUI (insight, décision) → L2 + L3 si architectural
│  └─ NON (temp) → L1 si <5min, oublier sinon
│
├─ Architectural decision ?
│  ├─ OUI → L3 + ADR document
│  └─ NON → L2 seulement
│
├─ Pattern répété 5+ fois ?
│  ├─ OUI → Créer Skill + store L3
│  └─ NON → L2 une seule fois
│
└─ Sensible / Secret ?
   ├─ OUI (API keys) → ❌ Ne jamais stocker, utiliser .env
   └─ NON → Procéder normalement
```

## When to Consolidate

**Consolidate automatiquement:**
- Avant `think("bootstrap")` (refresh memory)
- Après 20+ memory events stockés
- Weekly (lundi 00:00 UTC)

**Ne PAS consolider:**
- Données sensibles (secrets, passwords)
- Cache temporaire (L1 seulement)
- Duplicates existantes

## Integration with think()

```python
# think() charge automatiquement:
# 1. Recent L1 (Redis) - status en cours
# 2. Relevant L2 (PostgreSQL) - insights similarités
# 3. Related L3 (Neo4j) - architectural context

think("bootstrap")
# Retour: {L1: [...], L2: [...], L3: [...]}
```

## Memory Event Format

**Requis:**
```json
{
  "type": "insight|decision|pattern|error|note",
  "content": "Description claire et concise",
  "source": "agent_name|manual",
  "timestamp": "ISO8601",
  "layer": "L1|L2|L3",
  "priority": "critical|high|normal|low",
  "tags": ["tag1", "tag2"]
}
```

**Optionnel (si important):**
```json
{
  "relates_to": ["skill1", "pattern2"],
  "architectural": true,
  "recommendation": "Action à prendre"
}
```

## Examples

### Example 1: Insight (L2)
```json
{
  "type": "insight",
  "content": "Backend memory_service.py contient 3 méthodes duplicates avec graph_service.py. Consolidation possible.",
  "source": "debt_hunter",
  "layer": "L2",
  "priority": "high",
  "tags": ["duplication", "memory", "refactoring"],
  "recommendation": "Créer abstract service parent"
}
```

### Example 2: Architecture Decision (L3)
```json
{
  "type": "decision",
  "content": "Notifications temps réel = GraphQL Subscriptions (vs WebSocket)",
  "source": "architect",
  "layer": "L3",
  "priority": "critical",
  "tags": ["architecture", "notifications"],
  "architectural": true,
  "relates_to": ["skill/GraphQL", "pattern/real-time"]
}
```

### Example 3: Pattern (L3 + Skill)
```json
{
  "type": "pattern",
  "content": "Async service wrapper pattern: Service class + async methods + error handling + logging",
  "source": "code",
  "layer": "L3",
  "priority": "high",
  "tags": ["async", "pattern", "services"],
  "relates_to": ["memory_service", "graph_service", "voyage_service"],
  "recommendation": "Créer skill '01-common/async-service-wrapper' pour réutilisation"
}
```

## Consolidation Triggers

| Trigger | Action | Frequency |
|---------|--------|-----------|
| L1 Redis full (>1000 keys) | Prune old > 10 min | Real-time |
| 20+ L2 events | Consolidate + cleanup | Per session |
| Weekly | Full consolidation | Monday 00:00 UTC |
| Before `compact()` | Aggressive cleanup | Manual |

## No-Store Rules

**Jamais stocker:**
- API keys (utiliser .env)
- Passwords (utiliser secrets)
- Personal data
- Duplicate existante (check avant store)
- Données incomplètes/bruitées

## Integration Checklist

- [ ] Skills créées avec memory strategy
- [ ] Tasks retournent format JSON avec memory event
- [ ] Hooks automatiques capturent memory updates
- [ ] Consolidation weekly scheduled
- [ ] No duplicate enforcement (before store)
- [ ] L1 TTL enforced (5 min max)
- [ ] Sensible data filtering

## Next: Instructions Details

See `instructions.md` for detailed consolidation rules.
