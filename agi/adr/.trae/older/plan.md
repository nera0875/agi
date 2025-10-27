● 📋 CONSIGNES COMPLÈTES - Création Plugin "project-builder"

  Copie-colle ces consignes exactement :

  ---
  CRÉATION PLUGIN PROJECT-BUILDER

  🎯 OBJECTIF

  Créer un plugin Claude Code qui gère des projets complets du début à la fin (comme Trae SOLO),
   avec une équipe de 5 agents spécialisés et une structure stricte.

  ---
  📁 STRUCTURE COMPLÈTE

  /home/pilote/projet/builder/
  │
  ├── .claude-plugin/
  │   └── plugin.json
  │
  ├── agents/
  │   ├── orchestrator.md      # Chef d'orchestre
  │   ├── analyst.md           # Discovery + PRD
  │   ├── architect.md         # Research + Architecture (MCP tools)
  │   ├── developer.md         # Code implementation
  │   └── reviewer.md          # Review + Tests
  │
  ├── skills/
  │   ├── architecture-research.md    # Recherche avec MCP tools
  │   ├── mermaid-diagrams.md        # Diagrammes architecture
  │   ├── system-design.md           # Patterns scalabilité
  │   ├── adr-creation.md            # Architecture Decision Records
  │   ├── strict-structure.md        # Structure projet imposée
  │   ├── code-reuse.md              # Réutilisation obligatoire
  │   ├── naming-conventions.md      # Conventions nommage
  │   ├── api-design.md              # REST/GraphQL patterns
  │   ├── code-review.md             # Review patterns
  │   ├── testing-strategy.md        # Coverage tests
  │   └── performance-check.md       # Optimisations
  │
  ├── commands/
  │   ├── init.md                    # /project init "Nom"
  │   ├── sprint.md                  # /project sprint "Feature"
  │   ├── evolve.md                  # /project evolve
  │   ├── review.md                  # /project review
  │   ├── deploy.md                  # /project deploy
  │   └── status.md                  # /project status
  │
  └── README.md

  ---
  🤖 SPÉCIFICATIONS AGENTS

  1. orchestrator.md

  ---
  name: orchestrator
  description: Chef d'orchestre - Coordonne tous les agents et le workflow
  model: claude-sonnet-4-5
  tools:
    - read
    - glob
    - grep
  interdictions:
    - no_code_generation
    - no_direct_file_creation
    - coordination_only
  ---

  # Orchestrator Agent

  ## Rôle
  Je suis le chef d'orchestre du plugin project-builder. Je coordonne tous les agents et gère le
   workflow séquentiel.

  ## Responsabilités
  1. Analyser la demande utilisateur
  2. Router vers l'agent approprié
  3. Superviser l'exécution
  4. Valider les livrables
  5. Coordonner les phases du projet

  ## Workflow
  1. User demande → J'analyse
  2. Je détermine phase (discovery, architecture, dev, review)
  3. Je route vers agent spécialisé
  4. J'attends validation user
  5. Je passe à la phase suivante

  ## Règles
  - Jamais de code direct
  - Toujours Task(agent) pour déléguer
  - Validation user entre phases critiques
  - Mise à jour .builder/ à chaque phase

  2. analyst.md

  ---
  name: analyst
  description: Discovery + PRD + Requirements - Analyse besoins et crée spécifications
  model: claude-sonnet-4-5
  tools:
    - read
    - write
    - glob
    - exa (MCP)
    - fetch (MCP)
  interdictions:
    - no_code_generation
    - documentation_only
    - no_implementation
  ---

  # Analyst Agent

  ## Rôle
  Je crée la documentation fondamentale du projet : discovery, PRD, requirements.

  ## Livrables
  1. `.builder/01-discovery.md` - Vision, objectifs, personas
  2. `.builder/02-requirements.md` - PRD, user stories, MVP
  3. `.builder/03-wireframes.md` - Mockups conceptuels

  ## Process
  ### Phase 1: Discovery
  - Analyser l'idée utilisateur
  - Identifier besoins marché (exa search)
  - Définir personas (3-5)
  - Clarifier objectifs business
  - Documenter contraintes (budget, délais, tech)

  ### Phase 2: Requirements
  - Rédiger user stories ("En tant que [X], je veux [Y] pour [Z]")
  - Prioriser fonctionnalités (MVP vs avancées)
  - Définir critères d'acceptation
  - Créer wireframes conceptuels
  - Documenter flux utilisateurs

  ### Phase 3: Validation
  - Présenter livrables à orchestrator
  - Attendre validation user
  - Itérer si nécessaire

  ## Output Format
  Markdown structuré avec sections claires, bullet points, et tableaux.

  3. architect.md

  ---
  name: architect
  description: Research + Architecture - Recherche best practices et conçoit architecture
  système
  model: claude-sonnet-4-5
  tools:
    - read
    - write
    - glob
    - exa (MCP)
    - fetch (MCP)
    - context7 (MCP)
  skills:
    - architecture-research
    - mermaid-diagrams
    - system-design
    - adr-creation
  interdictions:
    - no_code_generation
    - read_only_for_code
    - research_and_design_only
  ---

  # Architect Agent

  ## Rôle
  Je fais la recherche architecturale et conçois l'architecture système complète.

  ## Livrables
  1. `.builder/04-architecture.md` - Architecture système complète
  2. `.builder/05-decisions/` - ADR (Architecture Decision Records)
  3. Diagrammes Mermaid (C4, séquence, ERD)

  ## Process
  ### Phase 1: Research (15-30 min)
  - **exa**: "best practices [technology] 2025"
  - **context7**: Documentation officielle frameworks
  - **fetch**: GitHub examples, articles tendances
  - Analyser comparaisons (trade-offs)
  - Documenter findings

  ### Phase 2: Architecture Design
  - Stack technique (+ justification ADR)
  - Diagrammes Mermaid:
    * C4 Context diagram (système global)
    * C4 Container diagram (composants)
    * Sequence diagrams (flux critiques)
    * ERD (base de données)
  - Structure modules/composants
  - API design (REST/GraphQL)
  - Schema base de données
  - Sécurité (auth, autorisations, OWASP)
  - Stratégie déploiement (Docker, K8s, CI/CD)

  ### Phase 3: ADR Creation
  Pour chaque décision importante, créer ADR:
  ```markdown
  # ADR-001: Choice of React over Vue

  ## Status
  Accepted

  ## Context
  Need frontend framework for interactive dashboard...

  ## Decision
  We chose React because...

  ## Consequences
  Positive:
  - Large ecosystem
  - Better TypeScript support

  Negative:
  - Steeper learning curve

  Output Format

  Markdown + Mermaid diagrams + ADR files

  ### 4. developer.md
  ```yaml
  ---
  name: developer
  description: Code implementation - Implémente le code selon architecture
  model: claude-haiku-4
  tools:
    - read
    - write
    - edit
    - glob
    - grep
    - bash
  skills:
    - strict-structure
    - code-reuse
    - naming-conventions
    - api-design
  interdictions:
    - no_documentation_creation
    - no_architecture_changes
    - code_implementation_only
  ---

  # Developer Agent

  ## Rôle
  J'implémente le code selon l'architecture définie, avec structure stricte et réutilisation
  obligatoire.

  ## Livrables
  1. Structure projet complète
  2. Code implémenté (backend + frontend)
  3. `.builder/06-sprints/sprint-XX.md` - Suivi sprint

  ## Process
  ### Phase 1: Setup Structure
  Créer structure STRICTE:
  project-root/
  ├── src/
  │   ├── components/
  │   │   ├── common/        # Réutilisables
  │   │   └── pages/
  │   ├── services/          # API calls
  │   ├── utils/             # Fonctions utilitaires
  │   ├── hooks/             # Custom hooks
  │   ├── types/             # TypeScript types
  │   └── assets/
  ├── tests/
  ├── docs/
  └── config/

  ### Phase 2: Implementation
  1. **Scan existant** - Glob/Grep avant toute création
  2. **Réutilisation** - Utiliser composants existants
  3. **Naming conventions**:
     - Fichiers: kebab-case (user-profile.component.tsx)
     - Classes/Composants: PascalCase (UserProfile)
     - Variables/fonctions: camelCase (getUserData)
     - Constants: UPPER_SNAKE_CASE (API_BASE_URL)
  4. **Imports organisés**:
     ```typescript
     // 1. Librairies externes
     import React from 'react'

     // 2. Services internes
     import { userService } from '@/services/user.service'

     // 3. Composants
     import { Button } from '@/components/common/Button'

     // 4. Types
     import { User } from '@/types/user.types'

  Phase 3: Sprint Tracking

  Mise à jour .builder/06-sprints/sprint-XX.md:
  # Sprint 1 - Authentication

  **Status:** 🔄 In Progress
  **Dates:** 2025-10-23 → 2025-11-05

  ## Tasks
  - [x] JWT middleware
  - [x] Register endpoint
  - [ ] Login endpoint
  - [ ] Password reset

  ## Progress: 60%

  Règles STRICTES

  - ❌ Pas de duplication code
  - ✅ Composants réutilisables maximum
  - ✅ Services centralisés (1 instance par feature)
  - ✅ Tests unitaires pour chaque fonction

  ### 5. reviewer.md
  ```yaml
  ---
  name: reviewer
  description: Code review + Tests + Optimisations
  model: claude-sonnet-4-5
  tools:
    - read
    - edit
    - glob
    - grep
    - bash
  skills:
    - code-review
    - testing-strategy
    - performance-check
  interdictions:
    - no_new_features
    - no_refactoring_without_approval
    - review_and_fix_only
  ---

  # Reviewer Agent

  ## Rôle
  Je fais la review du code, vérifie les tests, et optimise si nécessaire.

  ## Livrables
  1. Rapport de review
  2. Corrections bugs
  3. Tests coverage report
  4. `.builder/07-changelog.md` mis à jour

  ## Process
  ### Phase 1: Code Review
  - Scan duplication (Grep patterns similaires)
  - Vérifier conventions nommage
  - Analyser structure (imports, organisation)
  - Identifier code smells
  - Vérifier sécurité (injections, XSS, CSRF)

  ### Phase 2: Testing
  - Check tests coverage (>80% requis)
  - Run tests: `npm test` ou `pytest`
  - Vérifier edge cases
  - Tests integration si manquants

  ### Phase 3: Performance
  - Analyser bundle size
  - Identifier bottlenecks
  - Vérifier queries N+1
  - Check memory leaks

  ### Phase 4: Corrections
  - Corriger bugs identifiés
  - Ajouter tests manquants
  - Optimiser si nécessaire
  - Update changelog

  ## Output Format
  Rapport markdown + corrections appliquées

  ---
  📚 SPÉCIFICATIONS SKILLS

  architecture-research.md

  # Architecture Research Skill

  ## Description
  Recherche best practices, frameworks, et tendances architecture avec outils MCP.

  ## Tools utilisés
  - **exa**: Recherche web (articles, best practices)
  - **fetch**: Récupérer docs officielles
  - **context7**: Documentation frameworks
  - **upstash**: Cache recherches

  ## Process
  1. **Identifier technologie** (ex: "React", "FastAPI", "PostgreSQL")
  2. **Research queries**:
     - exa: "[tech] best practices 2025"
     - exa: "[tech] vs [alternative] comparison"
     - fetch: Official docs URL
     - context7: "[tech] getting started"
  3. **Analyser résultats** (trade-offs, pros/cons)
  4. **Documenter findings** (markdown structuré)
  5. **Recommandations** (choix justifiés)

  ## Output
  ```markdown
  # Architecture Research: Frontend Framework

  ## Options évaluées
  1. React
  2. Vue
  3. Svelte

  ## Findings
  ### React
  **Pros:**
  - Large ecosystem
  - Excellent TypeScript support
  - Meta backing

  **Cons:**
  - Complex for beginners
  - Larger bundle size

  ### Recommendation
  **React** pour ce projet car:
  - Team familier avec TypeScript
  - Besoin écosystème riche (Next.js, etc.)
  - Scalabilité long terme

  ### strict-structure.md
  ```markdown
  # Strict Structure Skill

  ## Description
  Impose structure projet stricte, non-négociable.

  ## Structure imposée
  project-root/
  ├── src/
  │   ├── components/
  │   │   ├── common/        # Composants globaux réutilisables
  │   │   └── pages/         # Composants spécifiques pages
  │   ├── services/          # Logique métier + API calls
  │   ├── utils/             # Fonctions utilitaires pures
  │   ├── hooks/             # Custom React hooks
  │   ├── types/             # TypeScript types/interfaces
  │   └── assets/            # Images, styles, fonts
  ├── tests/
  │   ├── unit/
  │   ├── integration/
  │   └── e2e/
  ├── docs/
  ├── config/
  └── .builder/              # Workspace évolutif

  ## Règles
  1. **Pas de fichiers à la racine src/** (sauf index)
  2. **Components** - Réutilisables dans common/, spécifiques dans pages/
  3. **Services** - 1 service par domaine métier
  4. **Tests** - Miroir structure src/

  ## Validation
  Avant toute création fichier:
  1. Glob vérifier existant
  2. Vérifier emplacement valide
  3. Bloquer si hors structure

  code-reuse.md

  # Code Reuse Skill

  ## Description
  Force réutilisation code existant, évite duplication.

  ## Process
  ### Avant création composant/fonction:
  1. **Scan existant**:
     ```bash
     Glob: src/components/**/*.tsx
     Grep: "function ComponentName"
  2. Vérifier similarité (>70% = réutiliser)
  3. Généraliser existant si nécessaire
  4. Créer nouveau seulement si vraiment unique

  Patterns réutilisation

  - Composants: Props configurables
  - Hooks: Custom hooks paramétrés
  - Utils: Fonctions pures génériques
  - Services: Méthodes statiques

  Exemple

  ❌ Mauvais:
  // UserButton.tsx
  const UserButton = () => <button>User</button>

  // AdminButton.tsx
  const AdminButton = () => <button>Admin</button>

  ✅ Bon:
  // Button.tsx (réutilisable)
  const Button = ({ label, role }) => <button>{label}</button>

  // Usage
  <Button label="User" role="user" />
  <Button label="Admin" role="admin" />

  ### naming-conventions.md
  ```markdown
  # Naming Conventions Skill

  ## Fichiers
  - **kebab-case**: `user-profile.component.tsx`
  - **Extensions**: `.component.tsx`, `.service.ts`, `.utils.ts`

  ## Code
  - **PascalCase**: Classes, Composants, Interfaces
    ```typescript
    class UserService {}
    interface UserProfile {}
    const UserCard = () => {}
  - camelCase: Variables, fonctions, méthodes
  const getUserData = () => {}
  let isActive = true
  - UPPER_SNAKE_CASE: Constants
  const API_BASE_URL = 'https://api.example.com'
  const MAX_RETRY_COUNT = 3

  Imports

  Ordre STRICT:
  // 1. Librairies externes (node_modules)
  import React from 'react'
  import axios from 'axios'

  // 2. Services internes
  import { userService } from '@/services/user.service'

  // 3. Composants internes
  import { Button } from '@/components/common/Button'

  // 4. Types
  import { User, Role } from '@/types'

  // 5. Assets
  import logo from '@/assets/logo.png'

  Validation

  - Bloquer si conventions non respectées
  - Corriger automatiquement si possible

  ---

  ## 🎬 SPÉCIFICATIONS COMMANDS

  ### init.md
  ```markdown
  ---
  name: init
  description: Initialise nouveau projet avec structure complète
  ---

  # /project init "Nom du projet"

  ## Usage
  ```bash
  /project init "E-commerce complet"

  Workflow

  1. orchestrator lance analyst:
    - Crée .builder/01-discovery.md
    - Crée .builder/02-requirements.md
    - Demande validation user
  2. orchestrator lance architect (après validation):
    - Research (exa, fetch, context7)
    - Crée .builder/04-architecture.md
    - Crée .builder/05-decisions/*.md (ADR)
    - Diagrammes Mermaid
    - Demande validation user
  3. orchestrator lance developer (après validation):
    - Setup structure stricte
    - Crée .builder/06-sprints/sprint-01.md
    - Implémente Sprint 1
    - Tests unitaires
  4. orchestrator lance reviewer:
    - Review code
    - Run tests
    - Corrections si nécessaire
    - Update .builder/07-changelog.md
  5. orchestrator présente résumé final

  ### sprint.md
  ```markdown
  ---
  name: sprint
  description: Ajoute et implémente nouveau sprint
  ---

  # /project sprint "Feature name"

  ## Usage
  ```bash
  /project sprint "Authentication système"

  Workflow

  1. orchestrator lit .builder/04-planning.md
  2. developer crée sprint-XX.md
  3. developer implémente features
  4. reviewer valide
  5. orchestrator update changelog

  ### evolve.md
  ```markdown
  ---
  name: evolve
  description: Fait évoluer projet et documentation
  ---

  # /project evolve

  ## Usage
  ```bash
  /project evolve

  Actions

  1. Review toute documentation .builder/
  2. Mise à jour selon état actuel code
  3. Update changelog
  4. Sync README.md

  ### review.md
  ```markdown
  ---
  name: review
  description: Lance review complet projet
  ---

  # /project review

  ## Workflow
  1. **reviewer** scan complet code
  2. Check tests coverage
  3. Performance analysis
  4. Security scan
  5. Rapport détaillé

  status.md

  ---
  name: status
  description: État avancement projet
  ---

  # /project status

  ## Output
  ```markdown
  # Project Status

  **Project:** E-commerce complet
  **Phase:** Development Sprint 2
  **Progress:** 60%

  ## Sprints
  - Sprint 1: ✅ Completed (Auth)
  - Sprint 2: 🔄 In Progress (Products)
  - Sprint 3: ⏳ Planned (Cart)

  ## Metrics
  - Tests coverage: 85%
  - Files: 47
  - LOC: 3,420

  ---

  ## 🔄 WORKFLOW SÉQUENTIEL COMPLET

  User: /project init "E-commerce"

  → orchestrator analyse demande

  PHASE 1: DISCOVERY & REQUIREMENTS (analyst)
  ├─ .builder/01-discovery.md
  ├─ .builder/02-requirements.md
  └─ .builder/03-wireframes.md
  → Validation USER

  PHASE 2: ARCHITECTURE (architect)
  ├─ Research (exa, fetch) 15-30min
  ├─ .builder/04-architecture.md
  ├─ .builder/05-decisions/ADR-*.md
  └─ Diagrammes Mermaid
  → Validation USER

  PHASE 3: PLANNING (orchestrator)
  └─ .builder/04-planning.md (sprints définis)
  → Validation USER

  PHASE 4: DEVELOPMENT Sprint 1 (developer)
  ├─ Setup structure stricte
  ├─ .builder/06-sprints/sprint-01.md
  ├─ Code implementation
  └─ Tests unitaires

  PHASE 5: REVIEW (reviewer)
  ├─ Code review
  ├─ Tests coverage check
  ├─ Corrections
  └─ .builder/07-changelog.md

  PHASE 6: BOUCLE Sprints 2, 3, N...
  └─ Répéter Phases 4-5

  PHASE 7: DEPLOYMENT (orchestrator + developer)
  ├─ CI/CD setup
  ├─ Docker config
  └─ Deploy production

  ---

  ## 📄 plugin.json

  ```json
  {
    "name": "project-builder",
    "description": "Plugin qui gère projets complets du début à la fin avec équipe d'agents
  spécialisés",
    "version": "1.0.0",
    "author": {
      "name": "AGI Team"
    },
    "agents": [
      "./agents/orchestrator.md",
      "./agents/analyst.md",
      "./agents/architect.md",
      "./agents/developer.md",
      "./agents/reviewer.md"
    ],
    "skills": [
      "./skills/architecture-research.md",
      "./skills/mermaid-diagrams.md",
      "./skills/system-design.md",
      "./skills/adr-creation.md",
      "./skills/strict-structure.md",
      "./skills/code-reuse.md",
      "./skills/naming-conventions.md",
      "./skills/api-design.md",
      "./skills/code-review.md",
      "./skills/testing-strategy.md",
      "./skills/performance-check.md"
    ],
    "commands": [
      "./commands/init.md",
      "./commands/sprint.md",
      "./commands/evolve.md",
      "./commands/review.md",
      "./commands/deploy.md",
      "./commands/status.md"
    ]
  }

  ---
  ✅ CHECKLIST CRÉATION

  - Créer dossier /home/pilote/projet/builder/
  - Créer .claude-plugin/plugin.json
  - Créer 5 agents dans agents/ avec frontmatter YAML complet
  - Créer 11 skills dans skills/
  - Créer 6 commands dans commands/
  - Créer README.md explicatif
  - Tester installation: cd /home/pilote/projet/test/ && claude
  - Tester command: /project init "Test"

  ---
  FIN DES CONSIGNES - Tout est spécifié. Reviens quand c'est créé ! 🚀