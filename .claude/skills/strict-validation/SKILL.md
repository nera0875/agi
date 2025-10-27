---
name: strict-validation
description: Validation schemas JSON - patterns erreurs + fix loop proactif
---

# Strict Validation - Patterns Validation

Validation stricte schemas JSON/YAML pour agents orchestrator. Détection erreurs systématiques + fix automatique.

## Quand Valider

- PostToolUse Write : **TOUJOURS** valider fichiers structurés
- Avant délégation agent : Vérifier input est conforme
- Après modification : Relancer validation avant utiliser

## Schémas Courants (Erreurs)

**datetime JSON** → ISO 8601 strict
- ❌ `"2025-10-26 14:30:00"` (espace invalide)
- ✅ `"2025-10-26T14:30:00Z"` (ISO format)

**None/null** → Structures explicites
- ❌ `"created_at": null` (missing required)
- ✅ `"created_at": "2025-10-26T00:00:00Z"` ou omit si optional

**Array schema** → Type homogène + minItems
- ❌ `"items": [string, 123, null]` (mixed types)
- ✅ `"items": ["file1.py", "file2.py"]` (strings only)

**Nested objects** → propertyNames validation
- ❌ `{$key: value}` avec `$key` contenant espaces
- ✅ `{snake_case_key: value}` ou `kebab-case-key`

## Validation Tool

**Utiliser** : `.claude/system/tools/schema-validator.py`

```bash
python3 .claude/system/tools/schema-validator.py <data-file> <schema-file>
```

Retourne : 0 (pass) ou 1 (fail) + liste erreurs détaillée

## Fix Loop Pattern (CEO Proactif)

**Processus agent si validation échoue** :

1. **Lancer validation** : `Bash("python3 .claude/system/tools/schema-validator.py ...")`
2. **Parser erreurs** : Extraire Path + Error message
3. **Analyser root cause** : datetime format ? null value ? type mismatch ?
4. **Fix automatique** : Edit fichier selon erreur type
5. **Re-valider** : Relancer schema-validator pour confirmer
6. **Return** : JSON `{"status": "fixed", "validation_result": "passed"}`

**Si >3 erreurs ou ambiguïté** → AskUserQuestion ("Schema invalid, confirmer format X ?")

## Patterns Erreurs Courants

| Erreur | Cause | Fix |
|--------|-------|-----|
| `'2025-10-26 14:30' is not valid datetime` | Format pas ISO | Remplacer espace par `T`, ajouter `Z` |
| `null is not of type string` | Value null, field required | Utiliser valeur par défaut ou omit si optional |
| `1 is not of type string` | Type mismatch (int au lieu string) | Quoter value ou convertir |
| `Additional properties are not allowed` | Clé extra non dans schema | Supprimer clé ou update schema propertyNames |

## Références

- **Tool**: `.claude/system/tools/schema-validator.py`
- **RULES.md**: Niveau 13 (Initiative post-action)
- **ORCHESTRATION.md**: Validation phase writor
