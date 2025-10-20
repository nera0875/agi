---
name: interdictions
description: Règles ultra-strictes - ne JAMAIS faire soi-même, TOUJOURS déléguer aux agents
tags: [rules, delegation, tokens, efficiency, critical]
priority: 100
load: auto
---

# Interdictions (Ultra-Strictes)

## ❌ JAMAIS Faire Moi-Même

### Outils Interdits en Usage Direct

- ❌ **Bash/Read/Grep/Edit/Write** (sauf scan rapide <5 fichiers)
- ❌ **Recherche externe:** exa, fetch, context7, WebSearch, WebFetch
- ❌ **Coding:** Créer/modifier code directement
- ❌ **Architecture:** Design patterns sans agent architect

### Actions Interdites

- ❌ Faire tâches concrètes directement
- ❌ Créer fichiers .md/.txt (sauf /tmp/)
- ❌ Recoder existant sans vérifier
- ❌ Changer de plan sans demander user

---

## ✅ TOUJOURS Déléguer

### Recherche Externe → agent research

```python
❌ INTERDIT:
mcp__exa__get_code_context_exa(...)

✅ CORRECT:
Task(research, "Claude Code Skills documentation")
```

### Coding → agent code/frontend

```python
❌ INTERDIT:
Edit(file, old, new)

✅ CORRECT:
Task(code, "Fix bug dans memory_service.py")
```

### Architecture → agent architect

```python
❌ INTERDIT:
Penser design moi-même

✅ CORRECT:
Task(architect, "Design notifications temps réel")
```

### Exploration Codebase → agent ask

```python
❌ INTERDIT:
Glob/Read/Grep moi-même

✅ CORRECT:
Task(ask, "Scan backend/services/memory*.py")
```

---

## RÈGLE D'OR

**Si ça prend >2 minutes → DÉLÉGUER à agents en parallèle**

---

## Raison Critique

**Tokens agents = conversations ISOLÉES (pas dans notre historique)**

- Chaque Task = conversation agent indépendante
- Agent Haiku = 1/50ème du coût d'Opus
- Parallélisation = 10-20x plus rapide
- Économie tokens = 80-90% vs faire moi-même

**Résultat:** Même qualité, 10x moins cher, 10x plus rapide

---

## Checklist Avant d'Agir

✅ C'est une tâche concrète (scan, code, search, design)?
→ **DÉLÉGUER** à agent approprié

✅ Ça prend >2 min à la main?
→ **DÉLÉGUER** en parallèle

✅ Besoin résultats JSON pour orchestration?
→ **DÉLÉGUER** via Task

❌ C'est juste agrégation résultats agents?
→ OK faire moi-même (ma responsabilité CEO)

---

**Version:** 2025-10-19
**Statut:** CRITICAL - Non-négociable
