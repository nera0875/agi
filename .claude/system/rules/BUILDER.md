# BUILDER - Création Agents/Skills

## Agent Pattern

**Taille BASE : ≤30 lignes, AJOUT : ≤30 lignes justifiés**

Structure obligatoire BASE :
- Frontmatter (name, description, tools, skills, model)
- Job unique (1 phrase)
- Instructions directes (3-5 bullet points max)
- Contraintes (2-3 interdictions)

Structure AJOUT (si nécessaire) :
```markdown
<!-- AJOUT YYYY-MM-DD: Raison justification (N lignes) -->
[Contenu additionnel ≤30 lignes]
```

Exemple :
```yaml
---
name: recon
description: Reconnaissance pentest - subdomains + ports
tools: Bash, Read, Write
skills: pentest-patterns
model: haiku
---

Job : Découvre subdomains et ports ouverts.

Instructions :
- Utilise nmap + subfinder
- Format output JSON
- Timeout 60s max

Contraintes :
- JAMAIS scan destructif
- Output JSON uniquement
```

## Skill Pattern

**Taille max selon type** :

**Skills implémentation** : ≤50 lignes
- Guides actions concrètes (ex: "comment créer agent")
- Instructions courtes et ciblées

**Skills documentation** : Pas de limite
- Référence complète systèmes (ex: claude-plugins)
- Documentation exhaustive OK
- Agents lisent via Read explicite (pas auto-discovery)

Structure obligatoire :
- Frontmatter (name, description)
- Concept (2-3 phrases)
- Patterns courts (bullet points)
- Zéro blabla

## Règle d'or

Si skill implémentation >50 lignes → split en 2.
Si skill documentation >50 lignes → OK si référence complète nécessaire.
