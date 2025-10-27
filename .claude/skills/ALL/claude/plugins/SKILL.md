---
name: claude-plugins
description: Documentation complète plugins Claude Code - structure, manifest, installation, patterns
---

# Claude Code Plugins - Documentation Complète

## Concept

Plugins Claude Code = extensions system permettant agents custom + features dynamiques. Framework officiel Anthropic pour création métier/domaine.

---

## 1. Architecture Plugins

### Structure Obligatoire

```
my-plugin/
├── plugin.json              # Manifest principal (OBLIGATOIRE)
├── agents/                  # Dossier agents
│   ├── agent-name.md       # Format: frontmatter + job + instructions
│   └── other-agent.md
├── skills/                  # Dossier skills
│   ├── skill-name/
│   │   ├── SKILL.md        # Contenu skill
│   │   └── data/           # Data optionnelle
│   └── other-skill/
└── commands/               # Dossier commands (optionnel)
    ├── command-name.md     # Format: frontmatter + help + handler
    └── other-command.md
```

### Convention Nommage

- **kebab-case UNIQUEMENT** : `my-plugin`, `agent-name`, `skill-name`, `command-name`
- **Zéro espaces, zéro underscores, zéro CamelCase**
- **Fichiers** : `SKILL.md` (caps), `*.md` (agents/commands)
- **Répertoires** : kebab-case strict

---

## 2. Plugin Manifest (plugin.json)

### Structure Obligatoire

```json
{
  "name": "my-plugin",
  "description": "Brève description du plugin",
  "version": "1.0.0",
  "author": "Author Name",
  "agents": [
    "agent-name-1",
    "agent-name-2"
  ],
  "skills": [
    "skill-name-1",
    "skill-name-2"
  ],
  "commands": [
    "command-name-1"
  ],
  "dependencies": {
    "core-skill-1": "1.0.0"
  }
}
```

### Champs Obligatoires

| Champ | Type | Validation |
|-------|------|-----------|
| `name` | string | kebab-case, 3-50 chars |
| `description` | string | 1 phrase, <100 chars |
| `version` | string | semver (x.y.z) |
| `author` | string | Nom personne/org |
| `agents` | array | Noms agents existants |
| `skills` | array | Noms skills existants |
| `commands` | array | Noms commands (optionnel) |
| `dependencies` | object | Plugins/skills requis |

### Validation Manifest

```bash
# Vérifier structure JSON
jq . plugin.json

# Vérifier agents listés existent
jq -r '.agents[]' plugin.json | while read agent; do
  test -f "agents/$agent.md" || echo "ERREUR: $agent manquant"
done

# Vérifier skills listés existent
jq -r '.skills[]' plugin.json | while read skill; do
  test -d "skills/$skill" || echo "ERREUR: skill/$skill manquant"
done
```

---

## 3. Agents (agents/*.md)

### Format Obligatoire

```yaml
---
name: agent-name
description: Brève description fonction agent
tools: [Tool1, Tool2, Tool3]
model: haiku
---

Job : Action unique en 1 phrase.

Instructions :
- Première instruction
- Deuxième instruction
- Troisième instruction max
```

### Frontmatter Champs

| Champ | Type | Obligatoire | Format |
|-------|------|-------------|--------|
| `name` | string | OUI | kebab-case |
| `description` | string | OUI | <100 chars |
| `tools` | array | NON | [Tool1, Tool2] ou [] |
| `model` | string | OUI | haiku \| sonnet |

### Tools Disponibles (Standard)

- `Read` : Lire fichiers
- `Write` : Créer fichiers
- `Edit` : Modifier fichiers
- `Glob` : Chercher fichiers patterns
- `Grep` : Chercher contenu
- `Bash` : Exécuter commandes terminal

### Exemple Complet

```yaml
---
name: code-analyzer
description: Analyse code Python - structure, imports, classes
tools: [Read, Glob, Grep]
model: haiku
---

Job : Scanne code Python et retourne structure hiérarchique.

Instructions :
- Utilise Glob pour trouver fichiers *.py
- Grep "^class " pour lister classes + méthodes
- Format output JSON: {files: [...], classes: [...]}
```

### Limite Taille

**MAXIMUM 30 lignes** (frontmatter + job + instructions)

---

## 4. Skills (skills/skill-name/SKILL.md)

### Format Obligatoire

```markdown
---
name: skill-name
description: Brève description concept
---

# Titre Skill

## Concept

2-3 phrases expliquant quoi/pourquoi.

## Patterns

- Pattern 1 : Description courte
- Pattern 2 : Description courte
- Pattern 3 : Description courte

## Exemple

```yaml
Exemple code/config si nécessaire
```
```

### Catégories Skills

**1. Skills Implémentation** (≤50 lignes)
- Guides actions concrètes
- Patterns code/config
- Checklist procédures
- Audience : executors (agents)

**2. Skills Documentation** (illimité)
- Référence systèmes
- Architecture expliquée
- Conventions complètes
- Audience : orchestrators + agents

### Organisateurs Skills

```
skills/
├── core/
│   ├── manifest-builder/SKILL.md
│   ├── workflow-orchestration/SKILL.md
│   └── yaml-conventions/SKILL.md
├── patterns/
│   ├── backend-patterns/SKILL.md
│   ├── frontend-patterns/SKILL.md
│   └── testing-patterns/SKILL.md
└── validation/
    ├── code-validator/SKILL.md
    └── architecture-validator/SKILL.md
```

### Règle Taille Critique

```
Skills IMPLÉMENTATION:
  ≤50 lignes → OK, keep as-is
  >50 lignes → SPLIT en 2 skills (A+B)

Skills DOCUMENTATION:
  >50 lignes → OK si référence complète
  Documentation = acceptable à split ou garder monolithe
```

---

## 5. Commands (commands/*.md) - Optionnel

### Format Obligatoire

```yaml
---
name: command-name
description: Brève description commande
handler: agent-name
---

# /command-name

Help text 1 ligne.

Usage:
  /command-name [args]

Details :
- Détail 1
- Détail 2
```

### Champs Frontmatter

| Champ | Type | Obligatoire |
|-------|------|-------------|
| `name` | string | OUI |
| `description` | string | OUI |
| `handler` | string | OUI (agent dispatcher) |
| `args` | array | NON |

### Limit Taille

**MAXIMUM 20 lignes** total

---

## 6. Installation Plugin

### Étape 1 : Placer Plugin

```bash
# Plugin dans répertoire agent
.claude/marketplaces/my-plugin/

# Structure
.claude/marketplaces/my-plugin/
├── plugin.json
├── agents/
├── skills/
└── commands/
```

### Étape 2 : Activer dans CLAUDE.md

```markdown
**Plugin** : my-plugin
**Agents** : agent-name-1, agent-name-2
**Skills** : skill-name-1, skill-name-2
**Commands** : /command-name-1
```

### Étape 3 : Tester Installation

```bash
# Vérifier manifest valide
jq . .claude/marketplaces/my-plugin/plugin.json

# Vérifier tous fichiers existent
jq -r '.agents[]' plugin.json | xargs -I {} test -f "agents/{}.md" && echo "OK"

# Lancer agent test
Task("my-plugin:agent-name", "Test message")
```

---

## 7. Patterns Création Plugins

### Pattern A : Plugin Analyse (Scan + Report)

**But** : Scanner codebase, générer rapports.

**Agents typiques** :
1. `recon` - Scanner initial, identify areas
2. `analyzer` - Analyse détaillée per area
3. `reporter` - Compile résultats

**Skills typiques** :
- `scan-patterns` - Patterns fichiers chercher
- `analysis-rules` - Rules évaluation
- `report-format` - Format output standardisé

**Exemple** : audit-security (scan vulns → report)

### Pattern B : Plugin Builder (Création Artefacts)

**But** : Créer code/config/docs.

**Agents typiques** :
1. `designer` - Plan architecture
2. `generator` - Crée fichiers
3. `validator` - Valide artefacts

**Skills typiques** :
- `code-templates` - Templates code
- `structure-rules` - Rules hiérarchie
- `validation-rules` - Règles qualité

**Exemple** : project-builder (crée projets complets)

### Pattern C : Plugin Orchestration (Workflow)

**But** : Coordonner multi-agents, manage état.

**Agents typiques** :
1. `orchestrator` - Route workflow
2. `executor-1`, `executor-2` - Travail parallèle
3. `validator` - Contrôle qualité

**Skills typiques** :
- `workflow-guide` - Phases séquence
- `state-manager` - Gère état
- `routing-logic` - Routing décisions

**Exemple** : project-builder (workflow séquentiel instructor→architect→executor→writor)

---

## 8. Lifecycle Plugin

### Création (CLI ou Manuel)

```bash
# Créer dossier plugin
mkdir -p .claude/marketplaces/my-plugin/{agents,skills,commands}

# Créer plugin.json
# Créer agents, skills, commands
```

### Activation

```bash
# Ajouter CLAUDE.md
Task("plugin-name:agent-name", "Première utilisation")
```

### Update

```bash
# Modifier agent/skill/command
Edit("agents/agent-name.md", old, new)

# Test avant production
Task("plugin-name:agent-name", "Test message")
```

### Validation Avant Merge

```bash
# Vérifier limits
wc -l .claude/marketplaces/my-plugin/agents/*.md      # Max 30 each
wc -l .claude/marketplaces/my-plugin/skills/*/SKILL.md # Max 50 impl each

# Vérifier naming
ls -R .claude/marketplaces/my-plugin/ | grep -v "kebab-case" && echo "ERREUR"

# Vérifier manifest
jq . .claude/marketplaces/my-plugin/plugin.json > /dev/null && echo "OK"

# Vérifier zéro fichiers parasites
find .claude/marketplaces/my-plugin -type f \
  ! -name "*.md" ! -name "*.json" ! -d "data" && echo "PARASITE TROUVÉ"
```

---

## 9. Best Practices

### Agents

- **Responsabilité unique** : 1 agent = 1 fonction clairement définie
- **Tools minimaux** : Utiliser SEULEMENT tools nécessaires
- **Job description** : Cristal clair, 1 phrase max
- **Instructions courtes** : 3-5 points, pas d'exemples sauf critique
- **Model choix** : haiku par défaut (95% cas), sonnet si besoin contexte large

### Skills

- **Concept clairement expliqué** : 2-3 phrases, zéro blabla
- **Patterns actionables** : Bullet points exécutables, pas théorie
- **Pas de redondance** : 1 skill = 1 concept unique
- **Bien organisée hiérarchie** : core/, patterns/, validation/, etc.

### Commands

- **Utilitaires simples** : 1 arg max, dispatch vers agent
- **Zéro logique complexe** : Commands = router, pas businesslogic
- **Help texte clair** : Usage example + détails

### Plugin Global

- **Manifest à jour** : TOUJOURS sync plugin.json vs fichiers réels
- **Zéro dépendances circulaires** : Plugin A → B OK, B → A INTERDIT
- **Version sémantique** : 1.0.0 initial, increment logiquement
- **Zéro fichiers parasites** : Aucun .backup, .tmp, .old, README
- **Documentation via skills** : Pas README.md dans plugin root (use SKILL.md)

---

## 10. Intégration Orchestrator

### Utilisation Plugin en Orchestration

```python
# Simple : invoquer agent
Task("my-plugin:agent-name", "Ordre précis")

# Orchestration : chain agents
Task("my-plugin:designer", "Design architecture")
# Attend résultat → Update plan.yaml
Task("my-plugin:builder", "Build selon plan.yaml")
Task("my-plugin:validator", "Valide qualité")
```

### Plugin avec Skill Orchestration

```python
# Lancer skill pour décider next step
Skill("workflow-guide", {"plugin": "my-plugin", "phase": "current"})
# Retourne JSON: {next_agent, action, blockers}

# Basé sur skill result
Task(f"my-plugin:{next_agent}", action)
```

### Plugin Dependencies

```json
{
  "dependencies": {
    "project-builder": "2.0.0",
    "core/workflow-orchestration": "1.0.0"
  }
}
```

Si plugin dépend autre plugin → orchestrator valide availability avant Task().

---

## Résumé Checklist Création Plugin

- [ ] `plugin.json` valide (jq . → OK)
- [ ] Agents (`agents/*.md`) ≤30 lignes each
- [ ] Agents all listed in plugin.json
- [ ] Skills (`skills/*/SKILL.md`) ≤50 lignes (implémentation)
- [ ] Skills all listed in plugin.json
- [ ] Commands (`commands/*.md`) ≤20 lignes (optionnel)
- [ ] Commands all listed in plugin.json
- [ ] Aucun fichier `.backup`, `.tmp`, `.old`, `README`
- [ ] Naming kebab-case uniquement
- [ ] CLAUDE.md updated avec plugin déclaration
- [ ] Test : Task("plugin-name:agent", "test") → success

---

**VERSION** : 1.0.0 (Aligné RULES.md, BUILDER.md, ORCHESTRATION.md)
**DATE** : 2025-10-26
**STATUT** : Documentation complète officielle plugins Claude Code
