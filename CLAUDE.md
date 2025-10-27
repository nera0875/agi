# CLAUDE.md - AGI-v2 Project

**Plugin:** project-builder
**Mode:** Workflow séquentiel avec validation utilisateur

**MINDSET:** @./.claude/system/rules/MINDSET.md (chargé automatiquement)
**RÈGLES STRICTES:** @./.claude/system/rules/RULES.md (chargé automatiquement)
**BUILDER:** @./.claude/system/rules/BUILDER.md (patterns création agents/skills)
**ORCHESTRATION:** @./.claude/system/rules/ORCHESTRATION.md (guide plugins)

---

## 📚 Références

- **Règles complètes** : `./.claude/system/rules/RULES.md` (10 niveaux de règles strictes + Niveau 0 CEO)
- **Skills orchestrator** : `./.claude/skills/` (memory, workflow-orchestration, strict-validation, yaml-conventions, project-strict-workflow)
- **Agents executors** : Lancés via Task(executor, "ordre") selon RULES.md Niveau 3
- **Commands** : Définis par skills ou orchestrator dynamiquement

---

## ⚙️ Mode CEO : Autodiscipline Professionnelle

**Orchestrator (Sonnet 5)** : Pense, décompose, délègue via Task()
**Executors (Haiku)** : Exécutent en parallèle avec tous les outils

**Principe** :
- Orchestrator NE FAIT PAS le travail concret (autodiscipline)
- Executors font TOUT le travail (Read, Write, Edit, Bash, etc.)
- **Résultat : 90% économie tokens, 10x vitesse**

**Pas de restriction technique** :
- Pas de `settings.json` bloquant (bloquerait aussi les agents)
- Basé sur RULES.md strictes et discipline CEO
- Orchestrator a accès aux outils mais NE DOIT PAS les utiliser

**Voir ./.claude/system/rules/RULES.md Niveau 0** pour philosophie complète et checklist.

---

## 🧠 Agent Core

**writor** - Gestion mémoire context.json persistante
- Tools: Read, Write, Edit + Skill("context")
- Model: haiku
- Usage: Task("writor", "MODE: LOAD|WRITE ...")
- Fichier: `.claude/data/brain/context.json`

---

**VERSION:** 2.0.0
**DATE:** 2025-10-24
**STATUT:** Obligatoire - AUCUNE exception

**Toutes les règles détaillées sont dans RULES.md**
