# Hook PreCompact - Consolidation Automatique Avant Context Compact

## Vue d'ensemble

Le hook `pre_compact_consolidation.py` exécute une **consolidation rapide de la mémoire** avant que Claude Code compacte le contexte de conversation. C'est comme faire une "micro-sieste" pour renforcer les souvenirs importants avant de les archiver.

## Trigger

Automatiquement exécuté quand:
- Claude Code détecte que la conversation va être compactée
- Context window approche de sa limite
- Avant archivage conversation

Configuré dans `.claude/settings.local.json` sous `pre-compact` hooks.

## Actions Effectuées (< 30 secondes)

### 1. Compression Conversations Anciennes (📦)
- Identifie conversations > 7 jours sans summary
- Les marque pour compression (batch operation)
- **Limit:** 10 conversations max (pour rester rapide)

### 2. Long-Term Depression (💤) - Affaiblissement
- Réduit `strength` des concepts non accédés depuis 14 jours
- `strength *= 0.95` (5% affaiblissement)
- Garde `strength > 0.3` (ne supprime pas les faibles)
- Appliqué à L2/L3 (mémoire long-terme)

### 3. Long-Term Potentiation (⚡) - Renforcement
- Augmente `strength` des concepts accédés aujourd'hui
- `strength = min(strength * 1.05, 1.0)` (5% renforcement, max 1.0)
- Appliqué à L1/L2 (mémoire court-moyen terme)

### 4. Health Check (🏥)
- Collecte stats L1/L2/L3
- Compute count + avg_strength par layer
- Loggue pour monitoring

## Output

Retourne JSON structuré:

```json
{
  "success": true,
  "timestamp": "2025-10-20T16:01:14.584752",
  "mode": "pre_compact_quick",
  "duration_seconds": 0.13,
  "actions": {
    "conversations_compressed": 5,
    "concepts_weakened": 42,
    "synapses_pruned": 0
  },
  "stats": {
    "l1": {"count": 150, "avg_strength": 0.85},
    "l2": {"count": 450, "avg_strength": 0.72},
    "l3": {"count": 1200, "avg_strength": 0.45}
  },
  "errors": []
}
```

## Stratégie L1/L2/L3

### L1 - Short-Term Memory (Conversation Actuelle)
- Redis + contexte window
- Forte (strength ~0.9)
- Renforcée quotidiennement si accédée
- **PreCompact:** Augmente si accédée aujourd'hui (+5%)

### L2 - Medium-Term Memory (Dernière Semaine)
- PostgreSQL concepts_l2 table
- Moyenne (strength ~0.7)
- Conservée si accédée régulièrement
- **PreCompact:** Affaiblit si non accédée 14j (-5%)

### L3 - Long-Term Memory (Historique)
- Neo4j graph + PostgreSQL archivage
- Faible mais importante (strength ~0.4-0.5)
- Patterns émergents
- **PreCompact:** Affaiblit si non accédée 14j (-5%)

## Exécution

### Manuelle (Test)
```bash
python3 cortex/hooks/pre_compact_consolidation.py
```

### Automatique
Exécutée automatiquement par Claude Code avant context compact.
Voir logs: `[PreCompact] ✅ PreCompact consolidation complete!`

## Timing

- **Duration Typical:** 0.1-2 secondes
- **Timeout Configured:** 30 secondes max
- **Non-blocking:** Si échoue, continue pas impact

## Erreurs Gracieuses

Si tables DB manquent (dev environment):
- Les operations sont skippées
- Log des warnings
- Hook retourne quand même `success: true`
- Pas d'exception lancée

En production, requiert:
- PostgreSQL avec tables: `conversations`, `concepts`
- Neo4j optionnel (pour synapses_pruned)

## Configuration

Ajouter/modifier dans `.claude/settings.local.json`:

```json
"pre-compact": [
  {
    "type": "command",
    "command": "python3 /home/pilote/projet/agi/cortex/hooks/pre_compact_consolidation.py",
    "description": "Quick memory consolidation before context compact"
  }
]
```

## Monitoring

Les results du hook sont:
1. Loggués en real-time (`[PreCompact]` prefix)
2. Stockés en JSON stdout
3. Capturable par le hook runner de Claude Code

Check dernière exécution:
```bash
tail -50 ~/.claude-logs/hooks.log | grep PreCompact
```

## Relation avec Autres Consolidations

### vs Consolidation Complète Nocturne
- **Complète** (`cortex/consolidation.py` @ 3am): Full audit + embeddings + compression
- **PreCompact** (avant context compact): Minimal, rapide, focus L1→L2→L3

### vs consolidate_conversation.py
- **consolidate_conversation:** Compresse une conversation spécifique en mémoire
- **PreCompact:** Gère memory health générale (LTD/LTP)

Les deux s'exécutent en série dans `pre-compact` hook.

## Performance

| Action | Complexity | Time |
|--------|-----------|------|
| Compression | Batch UPDATE | ~50ms |
| LTD | INDEX sur last_accessed | ~100ms |
| LTP | INDEX sur last_accessed | ~100ms |
| Health | GROUP BY aggregate | ~50ms |
| **Total** | **Sub-second** | **< 300ms** |

## Future Improvements

- [ ] Async compression avec Haiku summaries
- [ ] Neo4j synapses pruning
- [ ] Embeddings manquants regeneration
- [ ] Adaptive strength adjustment basé patterns
- [ ] Metrics export (Prometheus-like)

---

**Version:** 2025-10-20
**Auteur:** Claude Code AGI
**Status:** Production Ready
