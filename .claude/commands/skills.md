---
description: Display skills mindmap organized by categories without loading skill content
allowed-tools: Read
---

# Skills Directory

Reading skill categories from `.claude/skills/skills-map.json`...

## Core (6 skills)
Skills système fondamentaux - orchestration, validation, contexte
- **context** - Patterns contextualisation - quelles infos stocker, format, quand mettre à jour
- **manifest-builder** - Génère plugin.json - manifest complet avec tous composants
- **project-strict-workflow** - Workflow création projet avec validation stricte + CEO fix automatique
- **strict-validation** - Validation schemas JSON - patterns erreurs + fix loop proactif
- **workflow-orchestration** - Routing intelligent via templates + state.json - détermine phase/agent automatiquement
- **yaml-conventions** - Format YAML strict - ISO 8601, kebab-case, null handling

## Orchestration (6 skills)
Skills routage phases et état dynamique des projets
- **deployment-orchestration** - Complete reference for Docker, CI/CD, environment config, logging/monitoring, database migrations
- **git-tracker** - Track fichiers créés/modifiés pour state.json
- **phase-router** - Routing phases - mapping phase status to next agent
- **routing-guide** - How intelligent routing works - state-based agent selection
- **state-manager** - Update .plan/state.json avec état courant
- **workflow-guide** - How to use project workflow - phases and progression

## Validation (3 skills)
Skills validation architecture, code et progress tracking
- **architecture-validator** - Valide structure architecture.md - agents/skills/commands définition
- **code-validator** - Valide agents/skills/commands - tailles et structure
- **progress-tracker** - Calcule progress % et détecte blocages stagnation

## Patterns (5 skills)
Skills patterns technologiques - frameworks et conventions
- **backend-config-patterns** - Environment variables, database async connections, structured logging, Docker containerization patterns
- **frontend-testing-patterns** - Jest setup, React Testing Library patterns, component unit tests, E2E testing with Cypress/Playwright
- **python-fastapi-conventions** - FastAPI routing structure, Pydantic models, error handling, project layout patterns for backend implementations
- **react-frontend-patterns** - Complete reference for React 18, TypeScript, Hooks, state management, testing
- **react-typescript-conventions** - React functional components, TypeScript strict mode, folder structure, hooks patterns, state management

## Guides (4 skills)
Skills guides et analyse - besoins, standards, conventions
- **code-standards** - Pattern standards code - naming, structure, best practices
- **conventions-guide** - Plugin conventions - naming, structure, size limits
- **requirements-analysis** - Pattern analyse besoins - user stories, acceptance criteria, constraints, success metrics
- **requirements-analyzer** - Parse requirements.md - extract agents/skills/commands needed

## Productivity (4 skills)
Skills optimisation productivité TSA/HPI - temps, énergie, objectifs
- **energy-mapper** - Analyse patterns énergie HPI - pics, creux, burnout prevention
- **goal-tracker** - Track roadmap milliardaire - milestones, progress %, blockers detection
- **goals-planning** - Vision→Goals→Milestones→Tasks breakdown milliardaire
- **time-optimizer** - Optimisation time blocks TSA/HPI - Deep Work, Pomodoro, energy-aware scheduling

## Claude (8 skills)
Documentation Claude Code officielle - plugins, hooks, workflows, outputs
- **claude-hooks** - Complete guide to Claude Code hooks - PreToolUse, PostToolUse, and lifecycle events
- **claude-skills** - Complete reference for Claude Code skills - creation, usage patterns, and best practices
- **common-workflows** - Common workflows and patterns for Claude Code usage - productivity best practices
- **docs-map** - Complete Claude Code documentation map - 44 pages organized by category
- **headless** - Claude Code Headless Mode - Automation sans interface graphique
- **output-styles** - Guide complet des styles de sortie Claude Code - styles natifs, configuration, création custom
- **plugins** - Documentation complète plugins Claude Code - structure, manifest, installation, patterns
- **sub-agents** - Complete guide to creating and using specialized AI subagents in Claude Code for task-specific workflows and context management

## Claude MCP (1 skill)
Integration Model Context Protocol - MCP servers et configuration
- **claude-mcp** - Model Context Protocol - MCP servers integration, configuration, and management for Claude Code

---

**Total: 37 skills** | Last updated: 2025-10-26

Use `Skill('skill-name')` to load implementation skills or `Read('.claude/skills/category/skill-name/SKILL.md')` to read documentation.
