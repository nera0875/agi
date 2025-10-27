---
name: tech-radar
description: Tech Radar - classification adopt/trial/assess/hold technologies
---

# Tech Radar - Technology Lifecycle

Classification technologies selon maturité adoption (inspiré ThoughtWorks).

## Concept

Tech Radar = 4 quadrants classification technologies projet/équipe.

## Quadrants

### 1. ADOPT ✅

**Définition** : Technologies validées, production-ready, recommandées.

**Critères** :
- Utilisées ≥2 projets avec succès
- Team expertise ≥7/10
- Ecosystem mature (stars >10k, maintenance active)
- Zero CVE critiques non-patchés

**Examples** :
- Python 3.11+
- FastAPI
- PostgreSQL 15+
- Docker
- React 18+

### 2. TRIAL 🧪

**Définition** : Technologies prometteuses, tester sur projets non-critiques.

**Critères** :
- Utilisées 1 projet ou POC validé
- Team expertise 4-6/10
- Ecosystem croissant (trend +50% downloads 6 mois)
- Communauté active

**Examples** :
- Bun (runtime JS)
- Astro (framework)
- Turso (DB edge)
- HTMX

**Action** : Créer POC, évaluer DX, benchmarks.

### 3. ASSESS 🔍

**Définition** : Technologies watch list, veille active, pas encore testées.

**Critères** :
- Jamais utilisées en prod
- Hype communauté (HN front page, Twitter trends)
- Potentiel disruptif
- Pas de benchmarks internes

**Examples** :
- Nouvelle LLM (Gemini 2.0)
- Framework émergent
- Protocol nouveau (HTTP/3 widespread)

**Action** : Research, lire docs, suivre releases.

### 4. HOLD ⛔

**Définition** : Technologies déconseillées, deprecated, remplacées.

**Critères** :
- Maintenance arrêtée
- CVE critiques non-patchés
- Ecosystem dying (downloads -50% 6 mois)
- Superseded par alternative (ADR)

**Examples** :
- Python 2.7
- AngularJS (superseded Angular 2+)
- MongoDB 3.x (security issues)

**Action** : Migration plan si utilisé, bloquer nouveaux usages.

## Workflow Tech Radar

**Quarterly Review** (tous les 3 mois) :
```
1. List technologies actuelles (.plan/tech-radar.json)
2. Check metrics (downloads, CVE, maintenance)
3. Move technologies between quadrants:
   - ASSESS → TRIAL (si POC validé)
   - TRIAL → ADOPT (si prod success)
   - ADOPT → HOLD (si deprecated)
4. Add new ASSESS (veille techno)
5. Update .plan/tech-radar.json
6. Notify team (changelog)
```

## Format tech-radar.json

```json
{
  "updated": "2025-10-27",
  "quadrants": {
    "adopt": [
      {
        "name": "FastAPI",
        "category": "backend-framework",
        "since": "2024-01-15",
        "projects_count": 3,
        "team_expertise": 8.5,
        "notes": "Standard backend Python"
      }
    ],
    "trial": [
      {
        "name": "Bun",
        "category": "runtime",
        "since": "2025-10-01",
        "poc_status": "in-progress",
        "notes": "Tester performance vs Node.js"
      }
    ],
    "assess": [
      {
        "name": "Gemini 2.0",
        "category": "llm",
        "added": "2025-10-27",
        "reason": "Multimodal native, benchmarks prometteurs"
      }
    ],
    "hold": [
      {
        "name": "Python 3.8",
        "category": "language",
        "deprecated_since": "2024-10-01",
        "replacement": "Python 3.11+",
        "migration_deadline": "2025-12-31"
      }
    ]
  }
}
```

## Movement Triggers

**ASSESS → TRIAL** :
- Trigger: Research completed + POC planned
- Action: Create POC project

**TRIAL → ADOPT** :
- Trigger: POC success + production deployment
- Action: Update standards, documentation

**ADOPT → HOLD** :
- Trigger: EOL announced OR security issues OR better alternative
- Action: Migration ADR

**Any → HOLD** :
- Trigger: CVE critique + no patch
- Action: Immediate block

## Integration ADR

**Lien ADR ↔ Tech Radar** :
- ADR adoption nouvelle techno → Move ASSESS → TRIAL
- ADR migration techno → Move ADOPT → HOLD
- Tech Radar quarterly → Trigger ADR si movements

**Example** :
```
ADR-005: Migrate Python 3.8 → 3.11
Trigger: tech-radar.json Python 3.8 moved ADOPT → HOLD
```

## Veille Sources

**Daily** :
- GitHub Trending
- HackerNews front page

**Weekly** :
- Stack Overflow Trends
- NPM/PyPI top downloads

**Monthly** :
- ThoughtWorks Tech Radar
- InfoQ trends

**Quarterly** :
- Stack Overflow Developer Survey
- State of JS/Python surveys

## Output

**File**: `.plan/tech-radar.json`
**Update**: Quarterly (+ ad-hoc si critical)
**Owner**: tech-lead agent
