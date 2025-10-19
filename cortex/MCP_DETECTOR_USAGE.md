# MCP Detector - Usage Guide

Script Python pour détecter automatiquement les types MCP et générer des configurations registry prêtes à l'emploi.

## Installation

Le script est auto-contenu, aucune dépendance externe requise (utilise stdlib Python).

```bash
chmod +x /home/pilote/projet/agi/cortex/mcp_detector.py
```

## Types MCP Supportés

Le détecteur reconnaît automatiquement:

| Type | Pattern | Exemple | Commande |
|------|---------|---------|----------|
| **NPX** | `@org/package` | `@openai/mcp` | `npx -y @smithery/cli run @openai/mcp` |
| **HTTP** | `http://` ou `https://` | `https://api.example.com/mcp` | `curl -s https://api.example.com/mcp` |
| **Python** | Finit par `.py` | `/path/to/mcp.py` | `python3 /path/to/mcp.py` |
| **Node.js** | Finit par `.js` | `/path/to/mcp.js` | `node /path/to/mcp.js` |
| **Binary** | Chemin absolu + exécutable | `/usr/local/bin/mcp` | `/usr/local/bin/mcp` |

## Usage CLI

### Mode interactif simple

```bash
python3 mcp_detector.py "@openai/mcp"
```

Sortie:
```json
{
  "mcp": {
    "command": "npx",
    "args": ["-y", "@smithery/cli@latest", "run", "@openai/mcp"],
    "transport": "stdio",
    "tools": [],
    "category": "utility",
    "description": "Mcp MCP (npx)"
  }
}
```

### Avec credentials

```bash
python3 mcp_detector.py "@openai/mcp" --creds '{"OPENAI_API_KEY": "sk-xxx"}'
```

Sortie:
```json
{
  "mcp": {
    "command": "npx",
    "args": ["-y", "@smithery/cli@latest", "run", "@openai/mcp", "--openai-api-key", "sk-xxx"],
    "transport": "stdio",
    "tools": [],
    "category": "ai",
    "description": "Mcp MCP (npx)"
  }
}
```

### Exemples par type

#### NPX Package
```bash
python3 mcp_detector.py "@github/mcp" --creds '{"GITHUB_TOKEN": "ghp_xxx"}'
python3 mcp_detector.py "@slack/mcp"
python3 mcp_detector.py "@anthropic/mcp"
```

#### HTTP Service
```bash
python3 mcp_detector.py "https://api.smithery.ai/mcp"
python3 mcp_detector.py "https://custom-mcp.example.com"
```

#### Python Script
```bash
python3 mcp_detector.py "/home/pilote/projet/agi/cortex/memory/stdio_wrapper.py"
```

#### Node.js Script
```bash
python3 mcp_detector.py "/path/to/mcp.js"
```

#### Binary
```bash
python3 mcp_detector.py "/usr/local/bin/my-mcp-binary"
```

## Usage Python

### Import et usage basique

```python
from mcp_detector import MCPDetector

detector = MCPDetector()

# Détecter le type
mcp_type = detector.detect_type("@openai/mcp")
# Returns: "npx"

# Générer la config
config = detector.build_config(
    "@openai/mcp",
    credentials={"OPENAI_API_KEY": "sk-xxx"},
    description="OpenAI MCP",
    tools=["chat", "embeddings"],
    category="ai"
)

print(config)
# {
#   "mcp": {
#     "command": "npx",
#     "args": ["-y", "@smithery/cli@latest", "run", "@openai/mcp", "--openai-api-key", "sk-xxx"],
#     "transport": "stdio",
#     "tools": ["chat", "embeddings"],
#     "category": "ai",
#     "description": "OpenAI MCP"
#   }
# }
```

### Fonction convenience

```python
from mcp_detector import detect_and_config
import json

config = detect_and_config(
    "@github/mcp",
    credentials={"GITHUB_TOKEN": "ghp_xxx"},
    tools=["create_issue", "create_pr"],
    category="development"
)

print(json.dumps(config, indent=2))
```

### Exemples complets

#### Ajouter MCP au registry dynamiquement

```python
import json
from mcp_detector import detect_and_config

# Détecter et générer config
config = detect_and_config(
    "@stripe/mcp",
    credentials={"STRIPE_API_KEY": "sk_live_xxx"},
    tools=["create_customer", "create_payment"],
    category="payment"
)

# Charger registry existant
with open("/home/pilote/projet/agi/cortex/mcp-registry.json", "r") as f:
    registry = json.load(f)

# Ajouter nouvelle config
registry.update(config)

# Sauvegarder
with open("/home/pilote/projet/agi/cortex/mcp-registry.json", "w") as f:
    json.dump(registry, f, indent=2)
```

#### Batch processing

```python
from mcp_detector import detect_and_config
import json

mcps = [
    ("@openai/mcp", {"OPENAI_API_KEY": "sk-xxx"}, "ai"),
    ("@github/mcp", {"GITHUB_TOKEN": "ghp_xxx"}, "development"),
    ("@slack/mcp", {}, "communication"),
]

registry = {}

for mcp_input, creds, category in mcps:
    config = detect_and_config(
        mcp_input,
        credentials=creds,
        category=category
    )
    registry.update(config)

with open("mcp-registry.json", "w") as f:
    json.dump(registry, f, indent=2)
```

## API Référence

### MCPDetector Class

#### `detect_type(input_str: str) -> str`
Détecte automatiquement le type MCP.

**Paramètres:**
- `input_str`: String d'input (package, URL, chemin)

**Retour:** Type MCP ("npx", "http", "python", "nodejs", "binary")

**Lève:** `ValueError` si type non reconnu

```python
detector = MCPDetector()
mcp_type = detector.detect_type("@openai/mcp")  # "npx"
```

#### `build_config(...) -> Dict`
Génère la configuration MCP complète.

**Paramètres:**
- `input_str`: Input MCP
- `credentials`: Dict des credentials (optionnel)
- `name`: Nom custom du provider (optionnel)
- `description`: Description (optionnel)
- `tools`: Liste des tools (optionnel)
- `category`: Catégorie (optionnel)

**Retour:** Dict de configuration prêt pour le registry

```python
config = detector.build_config(
    "@openai/mcp",
    credentials={"OPENAI_API_KEY": "sk-xxx"},
    tools=["chat", "embeddings"],
    category="ai"
)
```

#### `detect_and_config(input_str, **kwargs) -> Dict`
Fonction convenience pour détecter et générer en une seule appel.

```python
config = detect_and_config("@openai/mcp", credentials={"OPENAI_API_KEY": "sk-xxx"})
```

## Configuration Output

La configuration générée est formatée pour le registry MCP:

```json
{
  "provider_name": {
    "command": "string",
    "args": ["array", "of", "arguments"],
    "transport": "stdio",
    "env": {
      "ENV_VAR": "value"
    },
    "tools": ["tool1", "tool2"],
    "category": "string",
    "description": "string"
  }
}
```

### Champs

- **command**: Commande à exécuter (npx, python3, node, curl, ou chemin binary)
- **args**: Arguments de la commande
- **transport**: Protocol MCP (toujours "stdio")
- **env**: Variables d'environnement (optionnel)
- **tools**: Liste des outils disponibles
- **category**: Catégorie (ai, database, communication, etc.)
- **description**: Description du MCP

## Gestion des Credentials

Les credentials sont traités différemment selon le type MCP:

### NPX
Convertis en flags de ligne de commande:
```python
# Input
credentials = {"OPENAI_API_KEY": "sk-xxx"}

# Output
args = [..., "--openai-api-key", "sk-xxx"]
```

### Python/Node.js/Binary
Définis comme variables d'environnement:
```python
# Input
credentials = {"DATABASE_URL": "postgresql://..."}

# Output
env = {"DATABASE_URL": "postgresql://..."}
```

### HTTP
Pas de credentials (ou passés en flags curl si besoin)

## Tests

Exécuter la suite complète de tests:

```bash
python3 -m pytest test_mcp_detector.py -v
```

Résultats: 29 tests passent avec succès

**Couverture:**
- Détection de tous les types MCP
- Parsing de packages NPX
- Extraction de noms de provider
- Génération de configurations
- Inférence de catégories
- Gestion des credentials
- Gestion d'erreurs

## Exemples Pratiques

### Ajouter Stripe au registry

```bash
python3 mcp_detector.py "@stripe/mcp" --creds '{"STRIPE_API_KEY": "sk_live_xxx"}'
```

### Intégrer custom Python MCP

```bash
python3 mcp_detector.py "/home/pilote/projet/agi/cortex/memory/stdio_wrapper.py" \
  --creds '{"DATABASE_URL": "postgresql://...", "REDIS_URL": "redis://..."}'
```

### Service HTTP personnalisé

```bash
python3 mcp_detector.py "https://my-mcp-service.example.com/v1"
```

### Ajouter au registry existant

```python
import json
from mcp_detector import detect_and_config

# Générer config
config = detect_and_config("@anthropic/mcp", credentials={"ANTHROPIC_API_KEY": "sk-xxx"})

# Charger et mettre à jour registry
with open("mcp-registry.json") as f:
    registry = json.load(f)

registry.update(config)

with open("mcp-registry.json", "w") as f:
    json.dump(registry, f, indent=2)
```

## Limitations et Notes

- Les credentials NPX sont passés en ligne de commande (à adapter selon les besoins)
- Les variables d'environnement Python/Node.js/Binary ne sont pas chiffrées
- Le détecteur suppose que les fichiers existent et sont accessibles
- Les binaires doivent avoir le flag exécutable défini
- Les catégories sont inférées automatiquement (peuvent être overridées)

## Troubleshooting

### "Cannot detect MCP type"
Vérifier que l'input match l'un des patterns reconnus.

### "File not found"
Vérifier que le chemin vers le fichier est correct et accessible.

### "File is not executable"
Pour les binaires: `chmod +x /path/to/binary`

### Credentials ne passent pas
- NPX: Vérifier que la clé est au format CONSTANT_CASE
- Python/Node: Vérifier les noms de variables d'environnement
