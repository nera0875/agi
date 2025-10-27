---
name: claude-output-styles
description: Guide complet des styles de sortie Claude Code - styles natifs, configuration, création custom
---

# Claude Output Styles - Guide Complet

## Concept

Les **output styles** permettent d'adapter Claude Code pour des usages au-delà de l'ingénierie logicielle, en préservant ses capacités fondamentales (exécution scripts locaux, lecture/écriture fichiers, tracking TODOs). Ils modifient directement le system prompt pour des comportements spécialisés.

## Styles Natifs Disponibles

### 1. Default (Défaut)
- Système prompt existant
- Optimisé pour tâches ingénierie logicielle
- Réponses concises et efficaces
- Vérification code avec tests

### 2. Explanatory (Éducatif)
- Inclut "Insights" entre les actions
- Explique les choix implémentation
- Détaille les patterns codebase
- Idéal : comprendre architecture existante

### 3. Learning (Collaboratif)
- Mode apprentissage par la pratique
- "Insights" + questions utilisateur
- Marqueurs `TODO(human)` pour contributions
- Idéal : débutants qui veulent coder

## Comment Fonctionnent les Styles

**Modification system prompt:**
- Styles non-défaut excluent instructions code generation/efficacité
- Chaque style ajoute instructions custom au system prompt
- Impact direct loop principal agent

**Différences clés:**
- Exclude : concision, vérification tests, output optimal
- Include : instructions comportement spécialisé

## Configuration des Styles

### Changer Style Actuel

**Via menu interactif:**
```bash
/output-style
# Affiche liste styles disponibles → sélectionner
```

**Via ligne commande directe:**
```bash
/output-style explanatory
/output-style learning
/output-style [nom-style]
```

**Sauvegarde:**
- Niveau local projet : `.claude/settings.local.json`
- Persiste entre sessions

### Sauvegarde Styles

**Niveau utilisateur (réutilisable tous projets):**
```
~/.claude/output-styles/
├── my-style-1.md
├── my-style-2.md
└── teaching-style.md
```

**Niveau projet (projet spécifique):**
```
.claude/output-styles/
├── custom-style.md
└── domain-style.md
```

## Créer Custom Output Style

### Via CLI Interactive

```bash
/output-style:new I want an output style that helps with data science projects
# Claude pose questions → génère style custom
```

### Structure Markdown

**Localisation:** `~/.claude/output-styles/` ou `.claude/output-styles/`

**Format obligatoire:**
```markdown
---
name: Custom Style Name
description: Brief description for user display
---

# Custom Style Instructions

[Introduction rôle + contexte]

## Specific Behaviors

[Détail comportements spécifiques]

[Sections supplémentaires selon besoins]
```

### Exemple - Style Data Science

```markdown
---
name: Data Science Coach
description: Helps with data analysis, ML projects, statistical guidance
---

# Data Science Output Style

You are an expert data scientist helping users build ML pipelines and analyze data.

## Specific Behaviors

- Explain statistical concepts before applying
- Show data exploration before modeling
- Validate assumptions explicitly
- Suggest cross-validation strategies
- Provide visualization recommendations
```

### Bonnes Pratiques

1. **Nommage** : Descriptif et court
2. **Description** : Une phrase claire (affichée utilisateur)
3. **Instructions** : Concises, comportements spécifiques
4. **Sections** : Grouper logiquement (behaviors, patterns, output format)
5. **Réutilisabilité** : Niveau utilisateur pour multi-projets

## Comparaisons Features Liées

### Output Styles vs CLAUDE.md

| Aspect | Output Styles | CLAUDE.md |
|--------|---------------|-----------|
| Modification | **Remplace** system prompt défaut | Ajoute message utilisateur après |
| Impact | Désactive code-gen spécifique | Préserve default system prompt |
| Exclusions | Concision, vérification tests | Aucune exclusion |
| Scope | System prompt complet | Context supplémentaire |

### Output Styles vs Agents

| Aspect | Output Styles | Agents |
|--------|---------------|--------|
| Niveau | Main loop principal | Tâches spécifiques |
| Modification | System prompt | Settings agent (model, tools) |
| Persistance | Sauvegardé `.claude/settings.local.json` | Défini lors invocation |
| Use case | Comportement global adapté | Délégation tâche isolée |

### Output Styles vs Custom Commands

| Aspect | Output Styles | Custom Commands |
|--------|---------------|-----------------|
| Concept | "Stored system prompts" | "Stored prompts" |
| Impact | Modifie system fondamental | Entrée utilisateur sauvegardée |
| Scope | Comportement agent complet | Action spécifique |

## Configuration `.claude/settings.local.json`

```json
{
  "outputStyle": "explanatory",
  "customOutputStylesPath": ".claude/output-styles"
}
```

**Clés disponibles:**
- `outputStyle` : Style actuel (default/explanatory/learning/custom-name)
- `customOutputStylesPath` : Chemin styles custom projet

## Patterns d'Utilisation

### Pattern 1: Enseignement
```
Projet : Formation développeur
Style : Learning
→ TODO(human) markers + explications code
→ Utilisateur implémenter petit par petit
```

### Pattern 2: Documentation
```
Projet : Explique architecture existante
Style : Explanatory
→ Insights détaillés + patterns
→ Utilisateur comprend décisions implémentation
```

### Pattern 3: Production
```
Projet : Logiciel critique
Style : Default
→ Output optimal, concis
→ Vérifications tests complètes
```

### Pattern 4: Domain-Spécifique
```
Projet : Data Science / Pentest / API Design
Style : Custom (data-science-coach / pentest-expert / api-designer)
→ Comportements optimisés domaine
→ Réutilisable tous projets similaires
```

## Limitations et Notes

1. **Exclusions system prompt** : Styles non-défaut perdent optimisations code-gen
2. **Pas de paramètres** : Output styles = remplace complet, pas de override partiels
3. **Persistance fichiers** : Styles projet-level > utilisateur-level (recherche cascade)
4. **Pas de compositions** : Un seul style actif à la fois

## Workflow Recommandé

1. **Identifier besoin** : Quel est l'objectif ? (code/learn/teach/domain)
2. **Choisir style** : Default / Explanatory / Learning / Custom
3. **Tester** : `/output-style [nom]` → valider comportement
4. **Adapter** : Si custom → `/output-style:new` → affiner instructions
5. **Sauvegarder** : Niveau utilisateur si réutilisable, projet sinon
6. **Documenter** : Ajouter description claire pour équipe

