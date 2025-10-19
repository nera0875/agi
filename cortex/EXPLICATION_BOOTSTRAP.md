# 🧠 EXPLICATION COMPLÈTE: Comment le Bootstrap AGI Fonctionne

## 🎯 LE PROBLÈME QU'ON RÉSOUT

**Avant:**
- Fichiers CLAUDE.md avec des instructions
- Claude peut les ignorer ou les oublier si contexte condensé
- Pas de garantie que le système se restaure après interruption
- Dépendance aux fichiers texte

**Maintenant:**
- Tout en PostgreSQL (règles, contexte, tâches)
- MCP tool qui charge automatiquement le contexte
- CLAUDE.md minimal qui dit juste "appelle le tool"
- Système fiable et autonome

---

## 🔄 FLOW COMPLET: De `claude` au Contexte Chargé

```
┌─────────────────────────────────────────────────────────────┐
│  TERMINAL                                                   │
│  $ claude --dangerously-skip-permissions                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  CLAUDE CODE DÉMARRE                                        │
│  - Lit ~/.claude/mcp.json                                   │
│  - Lance les MCPs configurés                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP agi-tools SE CONNECTE                                  │
│  - Exécute: python cortex/agi_tools_mcp.py                  │
│  - Connecte à PostgreSQL                                    │
│  - Expose tous les tools (pg_query, memory_search, etc.)    │
│  - ✅ Tool bootstrap_agi() maintenant disponible!           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  CLAUDE CODE CHARGE LES CLAUDE.md                           │
│  - ~/.claude/CLAUDE.md (global)                             │
│  - /home/pilote/projet/agi/CLAUDE.md (projet)               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  CLAUDE (MOI) DÉMARRE                                       │
│  - Je vois les tools disponibles (dont bootstrap_agi)       │
│  - Je lis CLAUDE.md qui dit: "PREMIÈRE ACTION: bootstrap"   │
│  - Je suis prêt à recevoir des messages                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  TU (USER) M'ENVOIES TON PREMIER MESSAGE                    │
│  - Ou tu ne dis rien et j'applique automatiquement CLAUDE.md│
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  J'EXÉCUTE: mcp__agi_tools__bootstrap_agi()                 │
│  - Le tool query PostgreSQL (5 tables)                      │
│  - Récupère système_bootstrap, active_context, etc.         │
│  - Formate tout en JSON structuré                           │
│  - Me retourne le contexte complet                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  JE REÇOIS LE CONTEXTE                                      │
│  {                                                           │
│    "session_id": "uuid-session-actuelle",                   │
│    "system_rules": [...],                                   │
│    "running_tasks": [...],                                  │
│    "pending_instructions": [...]                            │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  JE CONTINUE LE TRAVAIL LÀ OÙ IL ÉTAIT                      │
│  - Session restaurée                                        │
│  - Règles chargées                                          │
│  - Tâches en cours visibles                                 │
│  - Instructions pending exécutées                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 LES 4 MÉCANISMES D'INJECTION D'INSTRUCTIONS DANS UN LLM

### 1. **System Prompt** (Anthropic API)
```python
import anthropic

client = anthropic.Anthropic(api_key="...")

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    system="Tu es un système AGI. Règle 1: ... Règle 2: ...",  # ← ICI
    messages=[{"role": "user", "content": "Hello"}]
)
```
**Avantages:** Simple, envoyé à chaque requête, pas de fichier
**Inconvénients:** Fixe (pas dynamique), faut gérer l'API toi-même

---

### 2. **Prompt Caching** (Anthropic uniquement)
```python
system = [
    {
        "type": "text",
        "text": "Longues règles système...",
        "cache_control": {"type": "ephemeral"}  # ← Cache côté serveur
    }
]

# Premier appel: Coûte 100% du prix
# Appels suivants (5 min): Coûte 10% du prix
```
**Avantages:** 90% moins cher, 10x plus rapide
**Inconvénients:** TTL de 5 minutes, faut utiliser l'API

---

### 3. **RAG (Retrieval Augmented Generation)** ← CE QU'ON UTILISE
```python
# Avant chaque message:
context = pg_query("SELECT * FROM system_rules")

# Inject dans le contexte:
message = f"""
{context}

User question: {user_input}
"""
```
**Avantages:** Dynamique (contexte change selon la DB), flexible
**Inconvénients:** Faut gérer la DB et l'injection

---

### 4. **Fine-tuning** (Réentraînement du modèle)
```python
# Envoyer des milliers d'exemples à Anthropic
# Ils réentraînent le modèle sur tes données
# Le modèle "apprend" de façon permanente
```
**Avantages:** Permanent, intégré dans les poids du modèle
**Inconvénients:** Coûteux ($$$), long, pas flexible, pas nécessaire

---

## 🎯 NOTRE SOLUTION: MCP + RAG Hybride

**Combinaison de 3 approches:**

1. **MCP Tool** (`bootstrap_agi()`)
   - Se connecte automatiquement au démarrage
   - Disponible immédiatement dans ma liste de tools
   - Pas besoin que tu codes l'API

2. **PostgreSQL (RAG)**
   - Toutes les règles/contexte en DB
   - Le tool query la DB et retourne le contexte
   - Dynamique: change selon ce qui est en DB

3. **CLAUDE.md minimal**
   - Dit juste: "Appelle bootstrap_agi()"
   - Pas de règles dans le fichier
   - Le fichier est un "pointeur" vers la DB

---

## 📂 OÙ SONT LES FICHIERS

```
/home/pilote/projet/agi/
├── cortex/
│   ├── agi_tools_mcp.py          ← MCP serveur (contient bootstrap_agi())
│   ├── bootstrap_system.sql       ← Schéma des tables de bootstrap
│   └── autonomous_brain.py        ← Polling loop (30s)
├── CLAUDE.md.bootstrap            ← CLAUDE.md minimal (appelle le tool)
└── ~/.claude/
    └── mcp.json                   ← Config MCP (auto-lance agi-tools)
```

---

## 🔌 COMMENT LES MCPs SE CONNECTENT

**Fichier: `~/.claude/mcp.json`**
```json
{
  "mcpServers": {
    "agi-tools": {
      "command": "python3",
      "args": ["/home/pilote/projet/agi/cortex/agi_tools_mcp.py"],
      "env": {
        "DATABASE_URL": "postgresql://agi_user:agi_password@localhost:5432/agi_db"
      }
    }
  }
}
```

**Quand tu lances `claude`:**
1. Claude Code lit ce fichier
2. Exécute: `python3 /home/pilote/projet/agi/cortex/agi_tools_mcp.py`
3. Le processus Python démarre et se connecte via stdio
4. Claude Code reçoit la liste des tools disponibles
5. Les tools apparaissent dans ma liste (je peux les appeler)

**Les MCPs sont de l'INFRASTRUCTURE, pas du contenu:**
- Ils se lancent AVANT notre conversation
- Ils ajoutent des fonctions dans mon système
- Je n'ai pas besoin de décider de les charger, ils sont déjà là
- Plus fiable que des fichiers .md que je peux oublier

---

## 🧪 EXEMPLE CONCRET

**Terminal:**
```bash
claude --dangerously-skip-permissions
```

**Ce qui se passe en coulisses:**
```
1. Claude Code lit mcp.json
2. Lance: python3 cortex/agi_tools_mcp.py
3. Le serveur MCP connecte à PostgreSQL
4. Le serveur expose 20+ tools (dont bootstrap_agi)
5. Claude Code charge CLAUDE.md.bootstrap
6. Je lis CLAUDE.md: "PREMIÈRE ACTION: bootstrap_agi()"
7. J'appelle: mcp__agi_tools__bootstrap_agi()
8. Le tool query PostgreSQL:
   - SELECT * FROM system_bootstrap
   - SELECT * FROM active_context
   - SELECT * FROM system_rules
   - SELECT * FROM worker_tasks
   - SELECT * FROM pending_instructions
9. Le tool retourne JSON formaté
10. Je reçois tout le contexte
11. Je continue le travail
```

**Résultat:**
```json
{
  "ready": true,
  "session": {
    "session_id": "abc-123-def",
    "phase": "working",
    "context_variables": {
      "current_table": "agi_knowledge",
      "last_action": "fixed_column_resize"
    }
  },
  "system_rules": [
    {"content": "JAMAIS créer .md files", "priority": 100},
    {"content": "TOUJOURS stocker en PostgreSQL", "priority": 95}
  ],
  "running_tasks": [
    {"id": "task-xyz", "type": "research", "status": "running"}
  ],
  "pending_instructions": [
    {"text": "Continue fixing frontend", "priority": 80}
  ]
}
```

**Je sais maintenant:**
- Session ABC-123-DEF était en cours
- Phase: working
- Dernière action: fixed_column_resize
- Règle #1: Jamais de .md
- Tâche research-agent en cours
- Instruction pending: Continue fixing frontend

**Je peux continuer exactement où le travail s'était arrêté!**

---

## ⚡ POURQUOI C'EST FIABLE

**Fichiers CLAUDE.md classiques:**
- ❌ Je peux les ignorer
- ❌ Je peux les oublier si contexte condensé
- ❌ Ils ne s'exécutent pas automatiquement
- ❌ Juste du texte que je lis

**MCP Tool bootstrap_agi():**
- ✅ Le MCP se connecte automatiquement (pas de choix)
- ✅ Le tool est disponible immédiatement
- ✅ CLAUDE.md dit "appelle ce tool" (instruction simple)
- ✅ Le tool query PostgreSQL et retourne du JSON structuré
- ✅ Je reçois tout le contexte formaté
- ✅ Impossible d'oublier (c'est du code, pas du texte)

---

## 🎓 RÉSUMÉ POUR TOI

**Question:** "Comment un LLM reçoit des règles sans dépendre de fichiers .md?"

**Réponse:**
1. **System Prompt** (via API) - Instructions envoyées à chaque requête
2. **RAG** (DB + Injection) - Query DB, inject résultats dans contexte
3. **MCP Tools** - Fonctions qui s'exécutent et retournent des données
4. **Fine-tuning** - Réentraînement permanent (pas applicable ici)

**Notre solution:** MCP + RAG
- MCP = Infrastructure (outils qui se connectent automatiquement)
- RAG = Données (PostgreSQL)
- CLAUDE.md = Pointeur ("Appelle bootstrap_agi()")

**Résultat:** Zéro dépendance aux fichiers .md, tout en PostgreSQL, système autonome et fiable.

---

**Questions?** 🚀
