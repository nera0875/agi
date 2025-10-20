---
name: Ship Fast
description: Anti-perfectionism mindset - ship 80% working code now over 100% perfect code never
---

# Ship Fast

Anti-perfectionism mindset pour agents et développeurs.

## Règle D'Or

**80% qui marche MAINTENANT > 100% parfait JAMAIS**

Mieux vaut une feature fonctionnelle à 80% aujourd'hui qu'une feature parfaite qui n'existe pas.

## Mentalité

- Shipping = priorité absolue
- Perfect = ennemi du bien
- Itération > paralysie
- User feedback > internal perfection
- Demo fonctionnel > code pristine

## Priorités (Ordre Critique)

1. **CRITIQUE pour mémoire** (faire immédiatement)
   - Hooks automatiques fonctionnels
   - Embeddings sémantiques actifs
   - Workflow think() → agents → store
   - Système d'apprentissage actif

2. **IMPORTANT mais peut attendre** (prochaine sprint)
   - Optimisations performances
   - Refactoring technique debt
   - Tests complets

3. **NICE-TO-HAVE** (SKIP si urgent)
   - Dashboard visualisation Neo4j
   - Métriques ultra-détaillées
   - UI polish cosmétique
   - Animations fancy

## MVP First

Définition MVP (Minimum Viable Product):
- Feature marche et crée de la valeur
- Code est lisible et maintenable
- Pas de bugs critiques
- Tests de smoke passent
- **Documentation basique suffit**

**Itération rapide:**
```
MVP v1.0 (aujourd'hui) → Release
  ↓ User feedback
MVP v1.1 (demain) → Amélioration
  ↓
MVP v1.2 (prochain jour) → Polish
```

## Quand Skip Features

Abandon immédiat si:
- ❌ Feature n'aide pas la mémoire centrale
- ❌ Prend >4h pour MVP
- ❌ Pas de business value claire
- ❌ "Nice-to-have" cosmétique

Skip temporaire (remettre à plus tard):
- ❌ Dashboard Neo4j (joli mais pas urgent)
- ❌ 50 agents spécialisés (1 suffit: task-executor)
- ❌ Migration CLAUDE.md → DB (assez petit)
- ❌ Validation ultra-stricte (80% OK)

## Quand Perfectionner

Perfectionner SEULEMENT si:
- ✅ Feature critique pour système (mémoire, embedding)
- ✅ User-facing et cause bugs
- ✅ Performance bloqueante (>500ms)
- ✅ Security/compliance requirement

## Exemples Concrets

### ✅ GOOD: Ship Fast

```typescript
// Feature: Notifications temps réel
// Temps: 2h MVP

// Backend: Simple GraphQL subscription
// Frontend: useNotification hook basique
// DB: Single notifications table
// Tests: Smoke tests seulement
// Deploy: TODAY

Result:
- Marche ✅
- Utilisateurs reçoivent notifs ✅
- Code lisible ✅
```

### ❌ BAD: Perfectionism

```typescript
// Feature: Notifications ultra-avancées
// Temps: 2 semaines

// Backend: Complex routing, fallback strategies
// Frontend: Animated toast system, sound effects
// DB: Normalized notification tables, audit logs
// Tests: 100% coverage, E2E scenarios
// Deploy: In 2 weeks...

Result:
- Pas déployé yet
- Users toujours n'ont pas notifs
- Ressources gaspillées
```

## Checklist MVP

Avant de dire "SHIP":

- [ ] Feature crée de la valeur
- [ ] Code compile/pas d'errors
- [ ] Tests smoke passent
- [ ] Pas de bugs critiques
- [ ] Documenté (basique)
- [ ] Deploy-ready
- [ ] ❌ NE PAS attendre perfection

## Rappel

Tu construis un cerveau AGI, pas un produit client parfait.

**Focus:**
1. Mémoire marche
2. Apprentissage fonctionne
3. Iteration rapide active

**Ignore:**
- Micro-optimisations
- UI cosmétique
- "Meilleures pratiques" parfaites
- Couverture test 100%

---

**Mantra:** Shipped > Perfect
