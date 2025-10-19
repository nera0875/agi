#!/usr/bin/env python3
"""
Système de Neurotransmetteurs - Allocation Dynamique de Ressources
=================================================================

Comme cerveau humain: modulation dynamique selon contexte et besoin.

NEUROTRANSMETTEURS:
- GLUTAMATE: Excitateur → urgence/priorité → plus de ressources
- DOPAMINE: Récompense → renforcement fort → apprentissage accéléré
- GABA: Inhibiteur → économie → moins de ressources
- SEROTONIN: Régulateur → équilibre → prévient extrêmes

QUERY TYPES:
- urgent: Glutamate ↑, GABA ↓ → depth 3, threshold 0.1, top_k 12 (~800 tokens)
- interactive: Équilibré → depth 2, threshold 0.2, top_k 5 (~400 tokens)
- background: Glutamate ↓, GABA ↑ → depth 1, threshold 0.4, top_k 3 (~150 tokens)

FEEDBACK LOOP:
- Success → Dopamine ↑ → LTP boost ↑ → apprentissage plus rapide
- Failure → GABA ↑ → économie → moins de ressources prochaine fois
"""

import asyncpg
from typing import Dict
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class NeurotransmitterSystem:
    """
    Système neural de modulation dynamique des ressources.

    Comme cerveau: adapte allocation selon contexte et résultats.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def modulate(self, query_type: str, context: Dict = None) -> Dict:
        """
        Modulation neurotransmetteurs → paramètres adaptatifs

        Args:
            query_type: 'urgent', 'interactive', 'background'
            context: Contexte additionnel (optionnel)

        Returns:
            {
                'max_depth': int,
                'activation_threshold': float,
                'ltp_strength': float,
                'top_k': int,
                'glutamate': float,
                'dopamine': float,
                'gaba': float,
                'serotonin': float
            }
        """
        context = context or {}

        # 1. Récupérer état actuel neurotransmetteurs
        state = await self._get_state()

        # 2. Ajuster selon query_type
        if query_type == 'urgent':
            # URGENCE: Glutamate haut, GABA bas
            glutamate = 0.9
            gaba = 0.2
            dopamine = state['dopamine']
            serotonin = 0.5

        elif query_type == 'background':
            # ÉCONOMIE: GABA haut, Glutamate bas
            glutamate = 0.3
            gaba = 0.8
            dopamine = state['dopamine']
            serotonin = 0.6

        else:  # interactive (default)
            # ÉQUILIBRÉ: Modéré partout
            glutamate = 0.6
            gaba = 0.4
            dopamine = state['dopamine']
            serotonin = 0.5

        # 2.5. 🧘 SEROTONIN REGULATION - Prevent extreme arousal
        arousal = glutamate - gaba

        if arousal > 0.7:  # Trop excité → serotonin calme
            serotonin = min(0.9, serotonin + 0.1)
            glutamate = max(0.5, glutamate * 0.9)
            logger.info(f"🧘 Serotonin regulation: arousal too high ({arousal:.2f}), calming down...")

        elif arousal < -0.5:  # Trop inhibé → serotonin active
            serotonin = max(0.3, serotonin - 0.1)
            gaba = max(0.3, gaba * 0.9)
            logger.info(f"🧘 Serotonin regulation: arousal too low ({arousal:.2f}), activating...")

        else:  # Normal range → maintain homeostasis
            # Serotonin gradually returns to baseline (0.5)
            current_serotonin = float(state['serotonin'])
            if current_serotonin > 0.5:
                serotonin = max(0.5, current_serotonin - 0.02)
            elif current_serotonin < 0.5:
                serotonin = min(0.5, current_serotonin + 0.02)

        # 3. Calculer paramètres adaptatifs
        params = self._compute_parameters(
            glutamate=glutamate,
            dopamine=dopamine,
            gaba=gaba,
            serotonin=serotonin
        )

        # 4. Sauvegarder état
        await self._update_state(
            glutamate=glutamate,
            dopamine=dopamine,
            gaba=gaba,
            serotonin=serotonin,
            query_type=query_type
        )

        logger.info(
            f"🧠 Neurotransmitters modulated for {query_type}: "
            f"depth={params['max_depth']}, threshold={params['activation_threshold']:.2f}, "
            f"top_k={params['top_k']}, ltp={params['ltp_strength']:.2f}"
        )

        return params

    def _compute_parameters(
        self,
        glutamate: float,
        dopamine: float,
        gaba: float,
        serotonin: float
    ) -> Dict:
        """
        Calcule paramètres spreading activation depuis neurotransmetteurs.

        FORMULES (inspirées cerveau humain):
        - max_depth = 1 + round(2 * (glutamate - gaba))
            → Glutamate ↑ = chercher plus profond
            → GABA ↑ = chercher moins profond (économie)

        - activation_threshold = 0.5 - (glutamate - gaba) * 0.3
            → Glutamate ↑ = threshold plus bas (accepte plus)
            → GABA ↑ = threshold plus haut (rejette plus)

        - ltp_strength = 0.1 + dopamine * 0.2
            → Dopamine ↑ = renforcement plus fort

        - top_k = 3 + round(glutamate * 10)
            → Glutamate ↑ = retourner plus de résultats
        """
        # Convert to float for calculations
        glutamate = float(glutamate)
        dopamine = float(dopamine)
        gaba = float(gaba)
        serotonin = float(serotonin)

        # Arousal level (excitation globale)
        arousal = glutamate - gaba  # Range: -0.5 to +0.5

        # Max depth: 1 à 3
        max_depth = max(1, min(3, 1 + round(2 * arousal)))

        # Threshold: 0.1 à 0.5
        threshold = max(0.1, min(0.5, 0.5 - arousal * 0.4))

        # LTP strength: 0.1 à 0.3
        ltp_strength = max(0.1, min(0.3, 0.1 + dopamine * 0.2))

        # Top K: 3 à 15
        top_k = max(3, min(15, 3 + round(glutamate * 12)))

        return {
            'max_depth': int(max_depth),
            'activation_threshold': float(threshold),
            'ltp_strength': float(ltp_strength),
            'top_k': int(top_k),
            'glutamate': float(glutamate),
            'dopamine': float(dopamine),
            'gaba': float(gaba),
            'serotonin': float(serotonin),
            'arousal_level': float(arousal)
        }

    async def feedback(
        self,
        success: bool,
        response_time: int,
        tokens_used: int = 0
    ):
        """
        Feedback loop: ajuste neurotransmetteurs selon résultats.

        SUCCESS:
        - Dopamine ↑ (récompense) → LTP plus fort prochaine fois
        - GABA ↓ (moins d'inhibition)

        FAILURE:
        - Dopamine ↓
        - GABA ↑ (économie) → moins de ressources prochaine fois

        Args:
            success: Query réussie ou non
            response_time: Temps réponse en ms
            tokens_used: Nombre tokens utilisés
        """
        state = await self._get_state()

        # Current values
        dopamine = float(state['dopamine'])
        gaba = float(state['gaba'])
        serotonin = float(state['serotonin'])

        if success:
            # SUCCESS → Récompense
            dopamine = min(0.9, dopamine + 0.05)  # Boost dopamine
            gaba = max(0.2, gaba - 0.02)  # Moins d'inhibition
            serotonin = min(0.8, serotonin + 0.02)  # Équilibre

        else:
            # FAILURE → Économie
            dopamine = max(0.3, dopamine - 0.05)  # Moins de récompense
            gaba = min(0.9, gaba + 0.05)  # Plus d'inhibition
            serotonin = max(0.3, serotonin - 0.02)  # Déséquilibre

        # Update average response time
        avg_rt = state['avg_response_time'] or 0
        new_avg_rt = int((avg_rt * 0.9) + (response_time * 0.1))  # Moving average

        # Learning rate modulation
        learning_rate = float(state['learning_rate'])
        if success and response_time < 1000:  # Fast success
            learning_rate = min(0.3, learning_rate + 0.02)
        elif not success or response_time > 3000:  # Slow/failure
            learning_rate = max(0.05, learning_rate - 0.01)

        # Save updated state
        await self._update_state(
            dopamine=dopamine,
            gaba=gaba,
            serotonin=serotonin,
            last_query_success=success,
            avg_response_time=new_avg_rt,
            learning_rate=learning_rate
        )

        logger.info(
            f"🔄 Feedback: success={success}, rt={response_time}ms → "
            f"dopamine={dopamine:.2f}, gaba={gaba:.2f}, lr={learning_rate:.2f}"
        )

    async def _get_state(self) -> Dict:
        """Récupère état actuel neurotransmetteurs"""
        row = await self.db.fetchrow(
            "SELECT * FROM neurotransmitter_state ORDER BY id DESC LIMIT 1"
        )

        if not row:
            # Create default state
            await self.db.execute("""
                INSERT INTO neurotransmitter_state (
                    glutamate, dopamine, gaba, serotonin, arousal_level, learning_rate
                ) VALUES (0.5, 0.5, 0.5, 0.5, 0.5, 0.1)
            """)
            row = await self.db.fetchrow(
                "SELECT * FROM neurotransmitter_state ORDER BY id DESC LIMIT 1"
            )

        return dict(row)

    async def _update_state(self, **kwargs):
        """Met à jour état neurotransmetteurs"""
        # Build SET clause
        set_parts = []
        values = []
        param_idx = 1

        for key, value in kwargs.items():
            if value is not None:
                set_parts.append(f"{key} = ${param_idx}")
                values.append(value)
                param_idx += 1

        if not set_parts:
            return

        set_parts.append(f"updated_at = NOW()")

        query = f"""
            UPDATE neurotransmitter_state
            SET {', '.join(set_parts)}
            WHERE id = (SELECT id FROM neurotransmitter_state ORDER BY id DESC LIMIT 1)
        """

        await self.db.execute(query, *values)

    async def get_metrics(self) -> Dict:
        """Récupère métriques système neurotransmetteurs"""
        state = await self._get_state()

        return {
            'glutamate': float(state['glutamate']),
            'dopamine': float(state['dopamine']),
            'gaba': float(state['gaba']),
            'serotonin': float(state['serotonin']),
            'arousal_level': float(state['arousal_level']),
            'learning_rate': float(state['learning_rate']),
            'avg_response_time': state['avg_response_time'],
            'last_query_type': state['query_type'],
            'last_success': state['last_query_success'],
            'updated_at': state['updated_at'].isoformat() if state['updated_at'] else None
        }

    async def reset(self):
        """Reset neurotransmetteurs à valeurs par défaut (homeostasis)"""
        await self._update_state(
            glutamate=0.5,
            dopamine=0.5,
            gaba=0.5,
            serotonin=0.5,
            arousal_level=0.5,
            learning_rate=0.1
        )

        logger.info("🔄 Neurotransmitters reset to baseline (homeostasis)")
